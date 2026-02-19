# src/extraction/extractor.py

import logging
from typing import Optional

from src.parser.java.java_parser import JavaParser
from src.parser.java.java_ast_adapter import JavaASTAdapter

from src.ast.models import ASTTree

from src.extraction.page_object_extractor import PageObjectExtractor
from src.extraction.locator_extractor import LocatorExtractor
from src.extraction.action_mapper import ActionMapper
from src.extraction.assertion_mapper import AssertionMapper

from src.ir.builder.project_ir_builder import ProjectIRBuilder
from src.ir.models.project import Project


logger = logging.getLogger(__name__)


class IRExtractor:
    """
    Orchestrates:
        Parser → AST → Domain Extraction → IR Builders

    Responsibility:
        - Execute extraction pipeline for a single Java file
        - Produce IR Project model

    Non-Goals:
        - Graph building
        - Semantic resolution
        - Optimization
        - File writing
        - Validation
    """

    def __init__(self) -> None:
        # No global mutable state
        self._parser = JavaParser()
        self._adapter = JavaASTAdapter()

        self._page_extractor = PageObjectExtractor()
        self._locator_extractor = LocatorExtractor()
        self._action_mapper = ActionMapper()
        self._assertion_mapper = AssertionMapper()

        self._project_builder = ProjectIRBuilder()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def extract(self, file_path: str) -> Project:
        """
        Full MVP extraction pipeline.

        Args:
            file_path: Path to Java test file.

        Returns:
            Project IR model (Pydantic)
        """

        logger.info("Extraction started for file: %s", file_path)

        # 1️⃣ Parse
        compilation_unit = self._parser.parse(file_path)

        # 2️⃣ Adapt to canonical AST
        ast_tree: ASTTree = self._adapter.adapt(
            compilation_unit=compilation_unit,
            file_path=file_path,
        )

        # 3️⃣ Domain Extraction (MVP: sequential)
        pages = self._page_extractor.extract(ast_tree)
        targets = self._locator_extractor.extract(ast_tree)
        actions = self._action_mapper.map(ast_tree)
        assertions = self._assertion_mapper.map(ast_tree)

        # 4️⃣ Build IR Project
        project_ir = self._project_builder.build(
            file_path=file_path,
            pages=pages,
            targets=targets,
            actions=actions,
            assertions=assertions,
        )

        logger.info("Extraction completed for file: %s", file_path)

        return project_ir
