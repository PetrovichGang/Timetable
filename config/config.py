from environs import load_dotenv, Env
from pathlib import Path
import pytz

env = Env()
CWD = Path(__file__).parent.parent.absolute()
load_dotenv(Path(CWD, ".env"))

MONGODB_IP = env.str("MONGODB_IP")
MONGODB_PORT = env.int("MONGODB_PORT")
MONGODB_URL = f"mongodb://{MONGODB_IP}:{MONGODB_PORT}" if env.str("MONGODB_URL") == "0" else env.str("MONGODB_URL")
MONGODB_CERTIFICATE = env.str("MONGODB_CERTIFICATE")

RABBITMQ_IP = env.str("RABBITMQ_IP")
RABBITMQ_PORT = env.str("RABBITMQ_PORT")
RABBITMQ_USER = env.str("RABBITMQ_USER")
RABBITMQ_PASS = env.str("RABBITMQ_PASS")
RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_IP}/"
RABBITMQ_ENABLE = env.bool("RABBITMQ_ENABLE")

REDIS_HOST = env.str("REDIS_HOST")
REDIS_PORT = env.int("REDIS_PORT")
REDIS_ENABLE = env.bool("REDIS_ENABLE")

CORS_DOMAIN = env.str('CORS_DOMAIN', "*")
API_IP = env.str('TimeTable_API_IP')
API_PORT = env.int('TimeTable_API_PORT')
API_URL = f"http://{API_IP}:{API_PORT}/api"
API_TOKEN = env.str('TimeTable_API_TOKEN')
AUTH_HEADER={'Authorization': f'Bearer {API_TOKEN}'}

Schedule_URL = env.str("Schedule_URL")

MANUAL_LINK = env.str("MANUAL_LINK")
VK_TOKEN = env.str("VK_TOKEN")
VK_ADMINS_ID = [int(admin_id) for admin_id in env.list("VK_ADMINS_ID")]
VK_ID_UNHANDLED = [int(admin_id) for admin_id in env.list("VK_ID_UNHANDLED")]

TG_TOKEN = env.str("TG_TOKEN")
TG_DOMAIN = env.str("TG_DOMAIN")
TG_PATH = env.str("TG_PATH")

TIMEZONE = pytz.timezone(env.str("TimeZone"))
