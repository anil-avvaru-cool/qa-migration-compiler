import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


def ensure_directory(path: str | Path) -> Path:
    """
    Ensure directory exists.
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def read_text_file(path: str | Path) -> str:
    """
    Read text file safely.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info("Reading file: %s", file_path)
    return file_path.read_text(encoding="utf-8")


def write_text_file(path: str | Path, content: str) -> None:
    """
    Write text file safely.
    """
    file_path = Path(path)
    ensure_directory(file_path.parent)

    logger.info("Writing file: %s", file_path)
    file_path.write_text(content, encoding="utf-8")


def read_json_file(path: str | Path) -> Any:
    """
    Read JSON file safely.
    """
    text = read_text_file(path)
    return json.loads(text)


def write_json_file(path: str | Path, data: Any, indent: int = 2) -> None:
    """
    Write JSON file deterministically.
    """
    file_path = Path(path)
    ensure_directory(file_path.parent)

    logger.info("Writing JSON file: %s", file_path)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
        )
