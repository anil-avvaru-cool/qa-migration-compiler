# src/core/pipeline.py

import logging
from pathlib import Path
from typing import List, Optional

from src.parser.base_parser import BaseParser
from src.parser.java.java_ast_adapter import JavaASTAdapter
from src.extraction.extractor import IRExtractor
from src.ir.builder.project_ir_builder import ProjectIRBuilder
from src.ir.writer.file_writer import FileWriter
from src.ir.models.project import ProjectIR
from src.ast.models import ASTNode, ASTLocation, ASTTree

# Phase 2 additions
# from src.ir.validator.schema_validator import SchemaValidator


logger = logging.getLogger(__name__)


class IRGenerationPipeline:
    """
    Orchestrates the MVP compiler pipeline:

    Parser → AST Adapter → Extraction → IR Builder → (Optional) Validation → Writer
    """

    def __init__(
        self,
        parser: BaseParser,
        adapter: JavaASTAdapter,
        extractor: IRExtractor,
        ir_builder: ProjectIRBuilder,
        writer: FileWriter,
        # validator: Optional[SchemaValidator] = None,
    ):
        self.parser = parser
        self.adapter = adapter
        self.extractor = extractor
        self.ir_builder = ir_builder
        self.writer = writer
        # self.validator = validator

    # -------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------

    def run(
        self,
        project_name: str,
        source_language: str,
        source_files: List[str],
        output_path: str,
        compiler_version: str = "0.1.0",
    ) -> ProjectIR:
        """
        Execute full IR generation pipeline.
        """

        logger.info("IR pipeline started")
        logger.info("Project: %s", project_name)
        logger.info("Total source files: %d", len(source_files))

        all_tests: List[str] = []
        all_suites: List[str] = []
        all_environments: List[str] = []

        # Deterministic ordering
        for file_path in sorted(source_files):
            logger.info("Processing file: %s", file_path)

            # 1️⃣ Parse
            compilation_unit = self.parser.parse(file_path)

            # 2️⃣ Adapt to Canonical AST
            ast_node = self.adapter.adapt(
                compilation_unit                
            )

            ast_tree = ASTTree(
                root=ast_node,
                language=source_language,
                file_path=file_path)

            # 3️⃣ Extract Domain Model
            extraction_result = self.extractor.extract(
                ast_tree,
                project_name=project_name,
                source_language=source_language,)
            logger.debug("Extraction result ***: %s", extraction_result)

            all_tests.extend(extraction_result["tests"])
            all_suites.extend(extraction_result["suites"])
            all_environments.extend(extraction_result["environments"])

            logger.info(
                "Extraction completed | tests=%d suites=%d envs=%d",
                len(extraction_result["tests"]),
                len(extraction_result["suites"]),
                len(extraction_result["environments"]),
            )
        
        test_names = [test["name"] for test in all_tests]
        suite_names = [suite["name"] for suite in all_suites]
        environment_names = [env["name"] for env in all_environments]

        # 4️⃣ Build Project IR
        project_ir = self.ir_builder.build(
            project_name=project_name,
            source_language=source_language,
            tests=test_names,
            suites=suite_names,
            environments=environment_names,
            compiler_version=compiler_version,
        )

        logger.info("IR build completed")

        # 5️⃣ Optional Schema Validation
        # if self.validator:
        #     logger.info("Schema validation started")
        #     self.validator.validate(project_ir)
        #     logger.info("Schema validation passed")

        # 6️⃣ Write Output
        logger.debug(f"ProjectIR content ***: {project_ir}")
        self._write_output(project_ir, output_path)

        logger.info("IR pipeline finished successfully")

        return project_ir

    # -------------------------------------------------------------
    # INTERNALS
    # -------------------------------------------------------------

    def _write_output(self, project_ir: ProjectIR, output_path: str) -> None:
        """
        Serialize and write IR to disk.
        """

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Pydantic → dict
        data = project_ir.model_dump()

        self.writer.write(
            path=str(path),
            data=data,
        )

        logger.info("IR written to %s", output_path)
