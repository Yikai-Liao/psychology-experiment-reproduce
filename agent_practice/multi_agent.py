# agent_practice/multi_agent_langgraph.py

from __future__ import annotations

import os
import sys
from typing import Optional
from typing_extensions import TypedDict, Literal

from loguru import logger

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool
from openhands.sdk.conversation.response_utils import get_agent_final_response

from agent_practice.util import set_env

from langgraph.graph import StateGraph, START, END
from promptbind import with_prompt, PromptEntry

# ===================== 日志配置 =====================

# 先干掉默认 stderr 的 verbose 输出，再自己加
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
)

os.makedirs("logs", exist_ok=True)

# 两个文件 sink：按 extra.agent 路由
logger.add(
    "logs/main_agent.log",
    level="DEBUG",
    filter=lambda r: r["extra"].get("agent") == "main",
)
logger.add(
    "logs/reviewer_agent.log",
    level="DEBUG",
    filter=lambda r: r["extra"].get("agent") == "reviewer",
)

main_log = logger.bind(agent="main")
reviewer_log = logger.bind(agent="reviewer")


# ===================== OpenHands 初始化 =====================

set_env()

model_name = os.getenv("LLM_MODEL")
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")

logger.info(f"Model name: {model_name}")
logger.info(f"Base URL: {base_url}")

llm = LLM(
    model=model_name,
    api_key=api_key,
    # base_url=base_url,
    disable_vision=True,
    # stream=True,
)

# 主工作 Agent（你可以随时把 tools 打开）
main_agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TaskTrackerTool.name),
    ],
)

# Reviewer 就纯 LLM，不挂工具
reviewer_agent = Agent(llm=llm)

cwd = os.getcwd()
main_conv = Conversation(agent=main_agent, workspace=cwd)
reviewer_conv = Conversation(agent=reviewer_agent, workspace=cwd)

# TASK = "Plan a 3-day trip to London focusing on history and food."
MAX_ROUNDS = 3


# ===================== LangGraph State 定义 =====================

class TripPlanState(TypedDict):
    round: int                 # 当前轮次，从 0 开始
    done: bool                 # 是否完成（PASS 或达到最大轮次）
    last_proposal: Optional[str]   # 主 Agent 最新方案
    last_review: Optional[str]     # Reviewer 最新反馈


# ===================== LangGraph 节点实现 =====================

@with_prompt(key="planner")
def main_agent_node(x: PromptEntry, state: TripPlanState) -> TripPlanState:
    """
    调主 Agent，生成/更新旅行计划。
    把完整输出写到 main_agent.log，不在终端打印。
    """
    round_no = state["round"]

    if round_no == 0 and state["last_proposal"] is None:
        logger.info(f"[main_agent] Round {round_no}: 发送初始任务")
        main_conv.send_message(x.render())
    else:
        logger.info(f"[main_agent] Round {round_no}: 根据 reviewer 反馈更新计划")

    main_conv.run()
    proposal = get_agent_final_response(main_conv.state.events)

    # 写入专属 log 文件
    main_log.debug(f"=== Round {round_no} Proposal ===\n{proposal}\n")

    # 状态里只存引用，不打印
    return {
        **state,
        "last_proposal": proposal,
    }

@with_prompt(key="reviewer")
def reviewer_node(prompt: PromptEntry, state: TripPlanState) -> TripPlanState:
    """
    调 Reviewer，对计划进行严格审查。
    在 reviewer_agent.log 里记录完整反馈。
    """
    round_no = state["round"]
    proposal = state["last_proposal"] or ""

    logger.info(f"[reviewer] Round {round_no}: 审查当前计划")

    review_prompt = prompt.render(proposal=proposal)

    reviewer_conv.send_message(review_prompt)
    reviewer_conv.run()

    review_feedback = get_agent_final_response(reviewer_conv.state.events)

    # 写入 reviewer 日志
    reviewer_log.debug(f"=== Round {round_no} Review ===\n{review_feedback}\n")

    # 检查最后一行是 PASS 还是 Continue
    last_line = review_feedback.strip().splitlines()[-1].strip()
    is_pass = (last_line == "<<<PASS>>>")

    if is_pass:
        logger.info(f"[reviewer] Round {round_no}: 审查通过 (<<<PASS>>>)")
        done = True
        new_round = round_no
    else:
        logger.info(f"[reviewer] Round {round_no}: 审查未通过 (<<<Continue>>>)，反馈回主 Agent")
        done = False
        new_round = round_no + 1

        feedback_msg = (
            "The reviewer returned the following feedback:\n"
            f"{review_feedback}\n"
            "Please update the plan to address these issues."
        )
        main_conv.send_message(feedback_msg)

    return {
        **state,
        "last_review": review_feedback,
        "done": done,
        "round": new_round,
    }


def route_after_review(state: TripPlanState) -> Literal["loop", "stop"]:
    """
    Reviewer 节点之后的路由逻辑：
    - 如果 done=True -> stop
    - 如果轮次 >= MAX_ROUNDS -> stop
    - 否则继续 loop -> main_agent
    """
    if state["done"]:
        logger.info("[router] 检测到 done=True，终止图执行")
        return "stop"

    if state["round"] >= MAX_ROUNDS:
        logger.info(f"[router] 达到最大轮次 MAX_ROUNDS={MAX_ROUNDS}，终止图执行")
        return "stop"

    logger.info(f"[router] 继续下一轮 (round={state['round']})")
    return "loop"


# ===================== 搭建 LangGraph =====================

builder = StateGraph(TripPlanState)

builder.add_node("main_agent", main_agent_node)
builder.add_node("reviewer", reviewer_node)

# 入口：先跑 main_agent
builder.add_edge(START, "main_agent")
# main_agent 跑完必然交给 reviewer
builder.add_edge("main_agent", "reviewer")

# reviewer 决定继续 loop 还是 stop
builder.add_conditional_edges(
    "reviewer",
    route_after_review,
    {
        "loop": "main_agent",
        "stop": END,
    },
)

graph = builder.compile()


# ===================== 运行 =====================

if __name__ == "__main__":
    logger.info("启动多 Agent（OpenHands + LangGraph）示例")

    initial_state: TripPlanState = {
        "round": 0,
        "done": False,
        "last_proposal": None,
        "last_review": None,
    }

    final_state = graph.invoke(
        initial_state,
        config={"recursion_limit": 32},  # 防止死循环，正常情况下用不到上限
    )

    logger.info(
        "图执行结束：round={round}, done={done}",
        round=final_state["round"],
        done=final_state["done"],
    )
    logger.info("主 Agent 输出已写入 logs/main_agent.log")
    logger.info("Reviewer 输出已写入 logs/reviewer_agent.log")
