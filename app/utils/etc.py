from datetime import datetime
from pathlib import Path
from typing import Union
import hashlib


def unix_to_date(timestamp: int, fmt: str = '%d.%m %H:%M') -> str:
    return datetime.utcfromtimestamp(timestamp).strftime(fmt)


def create_dir_if_not_exists(path: Path) -> None:
    if not path.exists():
        path.mkdir()
        path.chmod(777)


def get_md5_hash(data: Union[str, bytes]) -> str:
    if not isinstance(data, bytes):
        data = data.encode()
    result = hashlib.md5(data)
    return result.hexdigest()
