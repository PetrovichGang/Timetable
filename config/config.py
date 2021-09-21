from pathlib import Path
from os import getenv
import environs

CWD = Path(__file__).parent.parent.absolute()
environs.load_dotenv(Path(CWD, ".env"))

DB_IP = getenv("TimeTable_DB_IP")
DB_PORT = getenv("TimeTable_DB_PORT")

DB_URL = f"mongodb://{DB_IP}:{DB_PORT}"
API_URL = f"http://{getenv('TimeTable_API_IP')}:{getenv('TimeTable_API_PORT')}/api"

Schedule_URL = getenv("Schedule_URL")