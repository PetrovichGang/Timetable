from databases import TimeTableDB
import loguru

logger = loguru.logger
db = TimeTableDB()

tags_metadata = [
    {
        "name": "Основное расписание",
        "description": "Методы работы с коллекцией: Основное расписание.",
    },
    {
        "name": "Изменения в расписание",
        "description": "Методы работы с коллекцией: Изменения в расписание."
    },
    {
        "name": "Producer",
        "description": "Отправка сообщений в RabbitMQ."
    },
    {
        "name": "VK",
        "description": "Методы работы с коллекциями: VKGroups и VKUsers."
    },
    {
        "name": "TG",
        "description": "Методы работы с коллекциями: TGChat."
    }
]