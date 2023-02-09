from typing import List, Optional, Iterable
from pathlib import Path

from loguru import logger
import httpx

from config import VK_USER_TOKEN, VK_ALBUM_ID, VK_GROUP_ID

AUTH_PARAMS = {
    "v": "5.131",
    "access_token": VK_USER_TOKEN
}


def _get_upload_server(group_id: int, album_id: int) -> Optional[str]:
    res = httpx.post(
        "https://api.vk.com/method/photos.getUploadServer",
        params={
            **AUTH_PARAMS,
            "group_id": group_id,
            "album_id": album_id,
        }
    )
    data = res.json()
    if data.get("error"):
        logger.error(
            f"VK image uploader: {res} {data}"
        )
    else:
        data = res.json()["response"]
        return data["upload_url"]

    return None


def _upload_files(upload_url: str, files: dict):
    res = httpx.post(
        upload_url,
        files=files
    )
    return res.json()


def _generate_attachment_string(
        attachment_type: str, owner_id: int, item_id: int, access_key: Optional[str] = None
) -> str:
    return f"https://vk.com/{attachment_type}{owner_id}_{item_id}{('_' + access_key) if access_key else ''}"


def upload_images(images_path: Iterable[Path], group_id: int = VK_GROUP_ID, album_id: int = VK_ALBUM_ID)\
        -> Optional[Iterable[str]]:
    """Загружает максимум 5 фотографий в альбом и возвращает ссылки на них"""
    upload_url = _get_upload_server(group_id, album_id)
    if upload_url is None:
        return None

    files = {}
    for i, file_source in enumerate(images_path):
        if i >= 5:
            break
        files[f"file{i + 1}"] = open(file_source, "rb")

    uploader = _upload_files(upload_url, files)

    res = httpx.post(
        "https://api.vk.com/method/photos.save",
        params={
            **AUTH_PARAMS,
            **uploader,
            "group_id": group_id,
            "album_id": album_id
        }
    )
    data = res.json()
    if data.get("error"):
        logger.error(f"VK image uploader: {res} {data}")
        return None

    photos = data["response"]

    logger.info(f"VK image uploader: images {[image.name for image in images_path[:5]]} uploaded")
    links = [
        _generate_attachment_string(
            "photo", photo["owner_id"], photo["id"], photo.get("access_key")
        )
        for photo in photos
    ]
    logger.info(f"VK image uploader: uploaded image links {links}")
    return links
