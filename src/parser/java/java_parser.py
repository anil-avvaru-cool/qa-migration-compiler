# src/parsers/java_parser.py

import logging
from typing import Optional

import javalang
from javalang.tree import CompilationUnit
from javalang.parser import JavaSyntaxError

from src.parser.base_parser import BaseParser


logger = logging.getLogger(__name__)


class JavaParser(BaseParser):
    """
    Java syntax parser.

    Responsibility:
        - Parse Java source code
        - Return javalang.tree.CompilationUnit

    Non-Goals:
        - AST transformation
        - Parent wiring
        - ID assignment
        - Graph generation
        - Semantic resolution
    """

    def parse(self, file_path: str) -> CompilationUnit:
        """
        Parse Java file and return CompilationUnit.

        Args:
            file_path: Path to Java file.

        Returns:
            javalang.tree.CompilationUnit
        """

        logger.info("Java parsing started: %s", file_path)

        try:
            source_code = self._read_file(file_path)

            # Tokenization
            tokens = list(javalang.tokenizer.tokenize(source_code))

            # Parsing
            parser = javalang.parser.Parser(tokens)
            compilation_unit: CompilationUnit = parser.parse()

            logger.info("Java parsing completed: %s", file_path)

            return compilation_unit

        except JavaSyntaxError as e:
            logger.error(
                "Java syntax error in %s at line %s: %s",
                file_path,
                getattr(e, "at", None),
                str(e),
            )
            raise

        except Exception as e:
            logger.exception("Unexpected parsing error in %s", file_path)
            raise
