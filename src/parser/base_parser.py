# src/parsers/base_parser.py

from abc import ABC, abstractmethod
from typing import Any
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Base parser contract.

    Responsibility:
        - Define parsing interface.
        - Enforce return type contract at implementation level.
    """

    @abstractmethod
    def parse(self, file_path: str) -> Any:
        """
        Parse a source file.

        Args:
            file_path: Path to source file.

        Returns:
            Language-specific AST root object.
        """
        raise NotImplementedError

    def _read_file(self, file_path: str) -> str:
        """
        Reads file content safely.

        Args:
            file_path: Path to file.

        Returns:
            File contents as string.
        """
        path = Path(file_path)

        if not path.exists():
            logger.error("File not found: %s", file_path)
            raise FileNotFoundError(file_path)

        logger.info("Reading file: %s", file_path)

        return path.read_text(encoding="utf-8")
