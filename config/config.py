from environs import load_dotenv, Env
from pathlib import Path

env = Env()
CWD = Path(__file__).parent.parent.absolute()
load_dotenv(Path(CWD, ".env"))

DB_IP = env.str("TimeTable_DB_IP")
DB_PORT = env.int("TimeTable_DB_PORT")
DB_URL = f"mongodb://{DB_IP}:{DB_PORT}"

API_IP = env.str('TimeTable_API_IP')
API_PORT = env.int('TimeTable_API_PORT')
API_URL = f"http://{API_IP}:{API_PORT}/api"
API_TOKEN = env.str('TimeTable_API_TOKEN')

Schedule_URL = env.str("Schedule_URL")

VK_TOKEN = env.str("VK_TOKEN")
TG_TOKEN = env.str("TG_TOKEN")