from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from config import CWD

__all__ = ["schedule"]

env = Environment(loader=FileSystemLoader(Path(CWD, "templates")))
schedule = env.get_template("schedule.txt")