import os
import openhands.sdk as hands

from loguru import logger
from typing import Literal
from pydantic import BaseModel
from promptbind import PromptEntry, with_prompt
from langgraph.graph import StateGraph, START, END
from openhands.sdk.conversation.response_utils import get_agent_final_response


from agent_practice.util import set_env, REPO_ROOT

def build_llm() -> hands.LLM:
    set_env()
    return hands.LLM(
        model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_API_KEY"),
        disable_vision=True,
    )


MAX_ROUNDS = 5
EMPTY_PROMPT_PATH = str((REPO_ROOT / "agent_practice/empty.j2").resolve())

# @dataclass
class TripPlanState(BaseModel):
    round: int
    done: bool
    proposals: list[str]
    reviews: list[str]

class TripPlanner:
    def __init__(self, llm: hands.LLM):
        self.agent = hands.Agent(llm=llm, tools=[], system_prompt_filename=EMPTY_PROMPT_PATH)
        self.conversation = hands.Conversation(agent=self.agent, visualizer=None)

    def __call__(self, state: TripPlanState) -> TripPlanState:
        logger.info(f"[Planner] Round {state.round} started")
        if len(state.reviews) > 0:
            self.send_feedback(state)
        else:
            self.send_init_info()

        self.conversation.run()

        state.proposals.append(
            get_agent_final_response(self.conversation.state.events)
        )
        logger.info(f"[Planner] Round {state.round}\n{state.proposals[-1]}")
        return state

    @with_prompt(key="planner")
    def send_init_info(self, prompt: PromptEntry) -> None:
        init_prompt = prompt.render()
        logger.info("[Planner] Round 0\n" + init_prompt)
        self.conversation.send_message(init_prompt)

    @with_prompt(key="feedback")
    def send_feedback(self, prompt: PromptEntry, state: TripPlanState) -> None:
        self.conversation.send_message(
            prompt.render(review=state.reviews[-1])
        )


class TripReviewer:
    def __init__(self, llm: hands.LLM):
        self.agent = hands.Agent(llm=llm, tools=[], system_prompt_filename=EMPTY_PROMPT_PATH)
        self.conversation = hands.Conversation(agent=self.agent, visualizer=None)

    @with_prompt(key="reviewer")
    def __call__(self, prompt: PromptEntry, state: TripPlanState) -> TripPlanState:
        self.conversation.send_message(
            prompt.render(proposal=state.proposals[-1])
        )
        self.conversation.run()
        state.reviews.append(
            get_agent_final_response(self.conversation.state.events)
        )
        logger.info(f"[Reviewer] Round {state.round}\n{state.reviews[-1]}")
        return state

    @staticmethod
    def route(state: TripPlanState) -> Literal["stop", "loop"]:
        state.round += 1
        last_line = state.reviews[-1].splitlines()[-1]
        if "<<<PASS>>>" in last_line or "<<<FAILED>>>" in last_line:
            state.done = True
        elif "<<<CONTINUE>>>" in last_line:
            state.done = False
        else:
            state.done = True

        if state.done:
            return "stop"

        if state.round >= MAX_ROUNDS:
            return "stop"
        return "loop"


def build_langgraph():
    builder = StateGraph(TripPlanState)
    llm = build_llm()
    planner = TripPlanner(llm)
    reviewer = TripReviewer(llm)
    builder.add_node("planner", planner)
    builder.add_node("reviewer", reviewer)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "reviewer")

    builder.add_conditional_edges(
        "reviewer",
        reviewer.route,
        {
            "loop": "planner",
            "stop": END
        }
    )

    graph = builder.compile()
    return graph


if __name__ == "__main__":
    graph = build_langgraph()
    init_state = TripPlanState(
        round=0,
        done=False,
        proposals=[],
        reviews=[],
    )

    final_state = graph.invoke(init_state)
