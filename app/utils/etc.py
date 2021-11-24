from datetime import datetime


def unix_to_date(timestamp: int, fmt: str = '%d.%m %H:%M') -> str:
    return datetime.utcfromtimestamp(timestamp).strftime(fmt)
