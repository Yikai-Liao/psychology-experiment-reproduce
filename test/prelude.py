import sys, os
from pathlib import Path
import openhands.sdk as hands
from dotenv import load_dotenv
from loguru import logger

REPO_ROOT = Path(__file__).parent.parent
ENV_FILE = os.path.join(REPO_ROOT, ".env")
EXAMPLE_WORKSPACE = hands.LocalWorkspace(
    working_dir= str(REPO_ROOT / "example_workspace")
)

sys.path.insert(0, str(REPO_ROOT))

def set_env():
    logger.debug(f"set_env using {ENV_FILE}")
    load_dotenv(dotenv_path=ENV_FILE)

set_env()

def build_llm() -> hands.LLM:
    return hands.LLM(
        model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("LLM_API_KEY"),
        disable_vision=True,
    )


__all__ = [
    "REPO_ROOT",
    "EXAMPLE_WORKSPACE",
    "build_llm"
]