import os
import openhands.sdk as hands
from openhands.tools.preset.default import get_default_tools
from openhands.workspace.docker.workspace import DockerWorkspace
from loguru import logger
from typing import Literal
from pydantic import BaseModel
from promptbind import PromptEntry, with_prompt
from langgraph.graph import StateGraph, START, END
from openhands.sdk.conversation.response_utils import get_agent_final_response
from pathlib import Path
import tempfile
import uuid
import json



from .state import ReproduceState

def read_file(workspace:  DockerWorkspace | hands.LocalWorkspace, path: str|Path, mode: Literal['r', 'rb']):
    assert mode in ('r', 'rb'), f"Mode {mode} is not supported, please use 'r' or 'rb'"
    with tempfile.NamedTemporaryFile() as tmp:
        workspace.file_download(
            source_path=os.path.join(workspace.working_dir, str(path)),
            destination_path=tmp.name,
        )
        return open(tmp.name, mode).read()

class PaperSummarizer:
    def __init__(self, llm: hands.LLM, workspace: DockerWorkspace | hands.LocalWorkspace) -> None:
        tools = get_default_tools(enable_browser=False)
        self.agent = hands.Agent(
            llm=llm,
            tools=tools,
        )
        self.conv = hands.Conversation(
            agent=self.agent,
            workspace=workspace
        )
        self.exp_name_path = "exp_name.json"
        self.workspace = workspace

    def load_paper(self, state: ReproduceState) -> str:
        return read_file(self.workspace, state.paper_dir / state.paper_name, 'r')


    @with_prompt()
    def extract(self, prompt: PromptEntry, state: ReproduceState) -> ReproduceState:
        self.conv.send_message(prompt.render(
            paper=self.load_paper(state),
            exp_name_path = self.exp_name_path
        ))
        self.conv.run()
        exp_names = json.loads(read_file(self.workspace, self.exp_name_path, 'r'))
        state.exp_names = exp_names
        return state

    @with_prompt()
    def image_details(self, prompt: PromptEntry, state: ReproduceState) -> ReproduceState:
        self.conv.send_message(prompt.render())
        self.conv.run()
        return state


