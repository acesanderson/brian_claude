from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import jinja2
from conduit.sync import Conduit
from conduit.core.prompt.prompt import Prompt

log_level = int(os.getenv("PYTHON_LOG_LEVEL", "2"))
levels = {1: logging.WARNING, 2: logging.INFO, 3: logging.DEBUG}
logging.basicConfig(level=levels.get(log_level, logging.INFO), format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SKILL_DIR = Path(__file__).parent
VAULT = Path(os.environ["MORPHY"])


def render_prompt(description: str) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(SKILL_DIR)))
    template = env.get_template("prompt.jinja2")
    return template.render(rich_description=description)


def generate_tutorial(description: str) -> str:
    prompt_text = render_prompt(description)
    conduit = Conduit.create(model="gemini3", prompt=Prompt(prompt_text))
    conversation = conduit.run()
    return conversation.content


def save_to_vault(content: str, filename: str) -> Path:
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    output_path = VAULT / filename
    output_path.write_text(content)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a technical tutorial and save to Obsidian.")
    parser.add_argument("--description", required=True, help="Rich description of the tutorial to generate")
    parser.add_argument("--filename", required=True, help="Output filename (with or without .md extension)")
    args = parser.parse_args()

    logger.info(f"Generating tutorial: {args.filename}")
    content = generate_tutorial(args.description)
    output_path = save_to_vault(content, args.filename)
    logger.info(f"Saved: {output_path}")
    print(str(output_path))


if __name__ == "__main__":
    main()
