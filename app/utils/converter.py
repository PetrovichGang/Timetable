from typing import Optional, Iterable
from zipfile import ZipFile
from pathlib import Path
import json

from loguru import logger
import httpx

from app.utils.etc import create_dir_if_not_exists
from config import PSPDFKIT_TOKEN

converter_instructions = {
    'parts': [
        {
            'file': 'document'
        }
    ],
    'output': {
        'pages': {"start": 0, "end": -1},
        'type': 'image',
        'format': 'jpg',
        'dpi': 144
    }
}


def _unpack_zip(zip_file: Path, output_folder: Path) -> None:
    with ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(output_folder)


def convert_pdf_to_jpg(file: Path, output_dir: Path, is_multipage: bool = False) -> Optional[Iterable[Path]]:
    path = output_dir / "images"
    create_dir_if_not_exists(path)

    name = file.name.rsplit(".", 1)[0]
    output_folder = path / name
    create_dir_if_not_exists(output_folder)
    output_filename = f"{name}.zip" if is_multipage else f"{name}.jpg"

    # dir is not empty
    if any(output_folder.iterdir()):
        logger.info(f"PSPDFKIT: File {file.name} skipped, was converted earlier")
        return tuple(output_folder.iterdir())

    with httpx.stream(
            "POST",
            "https://api.pspdfkit.com/build",
            headers={
                "Authorization": f"Bearer {PSPDFKIT_TOKEN}"
            },
            files={
                "document": open(file, "rb")
            },
            data={
                "instructions": json.dumps(converter_instructions)
            }
    ) as response:
        if response.status_code == 200:
            with open(output_folder / output_filename, "wb") as fd:
                for chunk in response.iter_bytes(chunk_size=8096):
                    fd.write(chunk)
            logger.info(f"PSPDFKIT {response.status_code}: File {file.name} convert to jpg")
            if is_multipage:
                _unpack_zip(output_folder / output_filename, output_folder)
                (output_folder / output_filename).unlink()
            return tuple(output_folder.iterdir())
        else:
            logger.error(f"PSPDFKIT Error {response.status_code}: {response.text}")
