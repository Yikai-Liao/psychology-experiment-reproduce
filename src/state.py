from pathlib import Path

from pydantic import BaseModel
from typing import List

class ReproduceState(BaseModel):
    paper_dir: Path
    paper_name: str
    exp_names: list[str] = []
    exp_name_path: Path = Path("exp_name.json")
    exp_design_path: Path = Path("exp_design.md")
    code_plan_path: Path = Path("code_plan.md")
    skip_code: bool = False
