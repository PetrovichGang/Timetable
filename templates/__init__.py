from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from config import CWD

__all__ = ["schedule", "schedule_markdown"]

env = Environment(loader=FileSystemLoader(Path(CWD, "templates")), trim_blocks=True, newline_sequence="\n", keep_trailing_newline=True)
schedule = env.get_template("schedule.txt")
schedule_markdown = env.get_template("schedule_markdown.txt")
