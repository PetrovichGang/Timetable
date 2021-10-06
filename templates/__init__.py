from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from config import CWD

__all__ = ["schedule"]

env = Environment(loader=FileSystemLoader(Path(CWD, "templates")), trim_blocks=True, newline_sequence="\n", keep_trailing_newline=True)
schedule = env.get_template("schedule.txt")