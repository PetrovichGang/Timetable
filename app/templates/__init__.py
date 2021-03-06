from jinja2 import Environment, FileSystemLoader
from config import CWD

__all__ = ["schedule", "schedule_markdown", "full_timetable", "full_timetable_markdown"]

env = Environment(loader=FileSystemLoader(CWD / "app" / "templates"), trim_blocks=True, newline_sequence="\n", keep_trailing_newline=True)
schedule = env.get_template("schedule.txt")
schedule_markdown = env.get_template("schedule_markdown.txt")

full_timetable = env.get_template("full_timetable.txt")
full_timetable_markdown = env.get_template("full_timetable_markdown.txt")
