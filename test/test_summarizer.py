from prelude import *
from pathlib import Path
from src.summarizer import PaperSummarizer
from src.state import ReproduceState

from src.monkey_patches import apply_reasoning_content_patch

apply_reasoning_content_patch()

def main():
    state = ReproduceState(
        paper_dir=Path("paper"),
        paper_name="paper.md",
    )

    module = PaperSummarizer(
        llm = build_llm(),
        workspace=EXAMPLE_WORKSPACE,
    )

    state = module.extract(
        state
    )
    state = module.image_details(state)
    print(state)

if __name__ == "__main__":
    main()