from datetime import datetime
from pathlib import Path


def unix_to_date(timestamp: int, fmt: str = '%d.%m %H:%M') -> str:
    return datetime.utcfromtimestamp(timestamp).strftime(fmt)


def create_dir_if_not_exists(path: Path) -> None:
    if not path.exists():
        path.mkdir()
        path.chmod(777)
