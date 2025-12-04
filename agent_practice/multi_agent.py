from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool
from agent_practice.util import set_env
from openhands.sdk.conversation.response_utils import get_agent_final_response
from loguru import logger
import os

set_env()

model_name = os.getenv("LLM_MODEL")
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")

logger.debug("Model name: {}".format(model_name))
logger.debug("API key: {}".format(api_key))
logger.debug("Base URL: {}".format(base_url))

llm = LLM(
    model=model_name,
    api_key=api_key,
    # base_url=base_url,
    disable_vision=True,
    # stream=True,
)

main_agent = Agent(
    llm=llm,
    # tools=[
    #     Tool(name=TerminalTool.name),
    #     Tool(name=FileEditorTool.name),
    #     Tool(name=TaskTrackerTool.name),
    # ],
)

reviewer_agent = Agent(
    llm=llm,
)

cwd = os.getcwd()
# 1. 初始化两个独立的对话
# 主工作 Agent
main_conv = Conversation(agent=main_agent, workspace=cwd)
# 审查 Agent (它的任务就是检查别人，不需要复杂的工具)
reviewer_conv = Conversation(agent=reviewer_agent, workspace=cwd)

# 初始任务
task = "Plan a 3-day trip to London focusing on history and food."
main_conv.send_message(task)

MAX_ROUNDS = 3
current_round = 0

print(f"--- Round {current_round + 1}: Starting Task ---")

while current_round < MAX_ROUNDS:
    # --- 步骤 A: 运行主 Agent ---
    main_conv.run()

    # 获取主 Agent 的最终输出
    # get_agent_final_response 是官方提供的工具函数，用于提取最后一条文本消息
    proposal = get_agent_final_response(main_conv.state.events)

    print(f"\n[Main Agent Proposal]:\n{proposal[:100]}...\n")  # 打印前100个字符示例

    # --- 步骤 B: 运行审查 Agent ---
    # 我们构建一个 Prompt，把主 Agent 的输出来给审查者看
    review_prompt = f"""
    You are a strict reviewer for a 3-day London travel plan.

    We will say that the plan **MEETS ALL CRITERIA** if and only if ALL of the following are true:

    1. **Budget**:
       - The plan must contain at least ONE explicit numeric price range for any category
         (e.g. hotel price per night, daily food cost, attraction ticket range, etc.).

    2. **Logistics**:
       - The plan must contain at least TWO of the following logistics details:
         - public transportation or travel card suggestions
         - ticket booking or fast-track tips
         - time-saving tips or advice on grouping nearby attractions

    3. **Specific Names**:
       - The plan must mention AT LEAST FIVE specific named places, such as:
         - restaurants, pubs, cafes, or markets
         - museums, historic sites, or attractions

    Now, read the following plan and check these conditions exactly as written above.

    At the end of your response:
    - If ALL of the above conditions are satisfied, output ONLY:
      <<<PASS>>>
    - Otherwise, output ONLY:
      <<<Continue>>>

    Do not explain your decision in the last line. The last line must contain ONLY one of the two tags above.

    --- PLAN TO REVIEW ---
    {proposal}
    """

    # 这是一个新的对话轮次，或者你可以复用同一个 conversation 来保持上下文
    # 如果想每次都从头审查，可以用 reviewer_conv.ask_agent(review_prompt) (无状态)
    # 如果想让审查者记得之前的批评，就用 send_message + run (有状态)
    reviewer_conv.send_message(review_prompt)
    reviewer_conv.run()

    review_feedback = get_agent_final_response(reviewer_conv.state.events)
    print(f"\n[Reviewer Feedback]:\n{review_feedback}\n")

    # --- 步骤 C: Python 逻辑判断 ---
    if "PASS" in review_feedback.splitlines()[-1]:
        print(">>> Review PASSED! Task Complete. <<<")
        break
    else:
        print(">>> Review FAILED. Sending feedback back to Main Agent... <<<")

        # --- 步骤 D: 将反馈打回给主 Agent ---
        feedback_msg = (
            f"The reviewer returned the following feedback:\n{review_feedback}\n"
            "Please update the plan to address these issues."
        )
        main_conv.send_message(feedback_msg)

        current_round += 1

if current_round >= MAX_ROUNDS:
    print(">>> Max rounds reached. Stopping execution. <<<")