# src/ir/writer/file_writer.py

import json
import logging
from pathlib import Path
from typing import Any, Dict


logger = logging.getLogger(__name__)


class FileWriter:
    """
    Responsible for serializing and writing IR JSON to disk.

    Strict responsibility:
        - Accept JSON-serializable dict
        - Persist to file
        - Ensure deterministic ordering
    """

    def write(self, path: str, data: Dict[str, Any]) -> None:
        """
        Write IR data to a JSON file.

        Parameters:
            path: Absolute or relative output file path
            data: JSON-serializable dictionary

        Raises:
            TypeError: If data is not JSON serializable
            OSError: If writing fails
        """

        logger.info("IR write started | path=%s", path)

        file_path = Path(path)

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    sort_keys=True,   # deterministic output
                    ensure_ascii=False,
                )
                f.write("\n")  # POSIX-friendly newline

        except TypeError as e:
            logger.error("JSON serialization failed: %s", str(e))
            raise

        except OSError as e:
            logger.error("File write failed: %s", str(e))
            raise

        logger.info("IR write completed | path=%s", path)
