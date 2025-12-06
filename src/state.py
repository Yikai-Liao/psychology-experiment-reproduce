from pathlib import Path

from pydantic import BaseModel
from typing import List

class ReproduceState(BaseModel):
    paper_dir: Path
    paper_name: str
    exp_names: list[str] = []
