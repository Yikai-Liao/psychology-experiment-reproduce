import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).parent.parent
ENV_FILE = os.path.join(REPO_ROOT, ".env")

def set_env():
    load_dotenv(dotenv_path=ENV_FILE)