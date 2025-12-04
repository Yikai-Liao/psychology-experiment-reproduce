import os

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool
from loguru import logger

from agent_practice.util import set_env

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
    # custom_llm_provider=True,
)

agent = Agent(
    llm=llm,
    tools=[
        Tool(name=TerminalTool.name),
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
    ],
)

cwd = os.getcwd()
conversation = Conversation(agent=agent, workspace=cwd)

conversation.send_message("Write 3 facts about the current project into FACTS.txt.")
conversation.run()
print("All done!")