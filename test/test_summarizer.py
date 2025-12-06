from prelude import *
from pathlib import Path
from src.summarizer import PaperSummarizer
from src.state import ReproduceState

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