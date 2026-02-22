# src/core/pipeline.py

import logging
from pathlib import Path
from typing import List, Optional

from src.parser.base_parser import BaseParser
from src.parser.java.java_ast_adapter import JavaASTAdapter
from src.extraction.extractor import IRExtractor
from src.ir.builder.project_ir_builder import ProjectIRBuilder
from src.ir.builder.test_ir_builder import TestIRBuilder
from src.ir.builder.suite_ir_builder import SuiteIRBuilder
from src.ir.builder.targets_ir_builder import TargetsIRBuilder
from src.ir.writer.file_writer import FileWriter
from src.ir.models.project import ProjectIR
from src.ir.models.data import TestDataIR
from src.ir.models.environment import EnvironmentIR
from src.ir.models.test import TestIR
from src.ir.models.suite import SuiteIR
from src.ir.models.targets import TargetIR
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
    ):
        """
        Execute full IR generation pipeline.
        """

        logger.info("IR pipeline started")
        logger.info("Project: %s", project_name)
        logger.info("Total source files: %d", len(source_files))

        all_tests: List[dict] = []
        all_suites: List[dict] = []
        all_environments: List[dict] = []
        all_targets: List[dict] = []

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

            all_tests.extend(extraction_result.get("tests", []))
            all_suites.extend(extraction_result.get("suites", []))
            all_environments.extend(extraction_result.get("environments", []))
            # targets may be contributed by page object and locator extractors
            all_targets.extend(extraction_result.get("targets", []))

            logger.info(
                "Extraction completed | tests=%d suites=%d envs=%d",
                len(extraction_result["tests"]),
                len(extraction_result["suites"]),
                len(extraction_result["environments"]),
            )
        
        test_names = [test["name"] for test in all_tests]
        suite_names = [suite["name"] for suite in all_suites]
        environment_names = [env.get("name") for env in all_environments]

        # 4️⃣ Build Project IR
        project_ir = self.ir_builder.build(
            project_name=project_name,
            source_language=source_language,
            tests=test_names,
            suites=suite_names,
            environments=environment_names,
            compiler_version=compiler_version,
        )

        # 5️⃣ Build detailed IR models (tests, suites, targets, environments, data)
        test_builder = TestIRBuilder()
        suite_builder = SuiteIRBuilder()
        targets_builder = TargetsIRBuilder()

        # Build suites first to obtain suite id mapping
        suites_ir: List[SuiteIR] = []
        suite_name_to_id = {}
        for extracted_suite in all_suites:
            suite_ir = suite_builder.build(extracted_suite)
            suites_ir.append(suite_ir)
            suite_name_to_id[extracted_suite.get("name")] = suite_ir.id

        # Build targets (normalize extracted target dicts first)
        normalized_targets = []
        for t in all_targets:
            # Locator entries from LocatorExtractor (strategy present)
            if "strategy" in t:
                normalized_targets.append({
                    "type": "locator",
                    # Prefer a human name if locator was assigned to a variable
                    "name": t.get("name") or t.get("id"),
                    "locator": t.get("locator") or t.get("strategy"),
                    "metadata": {"file_path": t.get("file_path"), "id": t.get("id")},
                })
            # Page objects: have 'name' and 'file_path'
            elif "name" in t and ("strategy" not in t and "type" not in t):
                normalized_targets.append({
                    "type": "page",
                    "name": t.get("name"),
                    "locator": None,
                    "metadata": {"file_path": t.get("file_path"), "id": t.get("id")},
                })
            else:
                # fallback generic mapping
                normalized_targets.append({
                    "type": t.get("type", "unknown"),
                    "name": t.get("name") or t.get("id"),
                    "locator": t.get("locator"),
                    "metadata": t,
                })

        targets_ir: List[TargetIR] = targets_builder.build(normalized_targets)

        # Build a mapping from normalized target name -> deterministic target id
        target_name_to_id = {}
        for i, t_ir in enumerate(targets_ir):
            src_name = normalized_targets[i]["name"]
            target_name_to_id[src_name] = t_ir.id

        # Build tests, linking to suite ids when possible (tests need target mapping)
        tests_ir: List[TestIR] = []
        for extracted_test in all_tests:
            # determine suite id by searching suites that list this test
            suite_id = None
            for s in all_suites:
                if extracted_test.get("name") in s.get("tests", []):
                    suite_id = suite_name_to_id.get(s.get("name"))
                    break

            test_ir = test_builder.build(extracted_test, suite_id=suite_id, target_name_to_id=target_name_to_id)
            tests_ir.append(test_ir)

        # Build environments
        environments_ir: List[EnvironmentIR] = []
        from src.utils.hashing import deterministic_hash

        for env in all_environments:
            env_name = env.get("name")
            env_id = deterministic_hash(f"env::{env_name}")
            env_ir = EnvironmentIR(id=env_id, name=env_name, base_url=env.get("base_url"), variables=env.get("variables", {}))
            environments_ir.append(env_ir)

        # Build data (if present) — extracted tests may reference data, but extraction currently
        # does not produce a separate data list. Keep placeholder empty list for now.
        data_ir: List[TestDataIR] = []

        logger.info("IR build completed")

        # 5️⃣ Optional Schema Validation
        # if self.validator:
        #     logger.info("Schema validation started")
        #     self.validator.validate(project_ir)
        #     logger.info("Schema validation passed")

        # 6️⃣ Write Output — write a composite structure with all IR pieces
        output_data = {
            "project": project_ir.model_dump(),
            "tests": [t.model_dump() for t in tests_ir],
            "suites": [s.model_dump() for s in suites_ir],
            "targets": [t.model_dump() for t in targets_ir],
            "data": [d.model_dump() for d in data_ir],
            "environments": [e.model_dump() for e in environments_ir],
        }

        logger.debug("Composite structure with all IR pieces: %s", output_data)

        logger.debug("ProjectIR content ***: %s", project_ir)
        self._write_output(output_data, output_path)

        logger.info("IR pipeline finished successfully")

        # Return rich IR objects for programmatic use
        return {
            "project": project_ir,
            "tests": tests_ir,
            "suites": suites_ir,
            "targets": targets_ir,
            "data": data_ir,
            "environments": environments_ir,
        }

    # -------------------------------------------------------------
    # INTERNALS
    # -------------------------------------------------------------

    def _write_output(self, project_ir_or_data, output_path: str) -> None:
        """
        Serialize and write IR to disk.
        """

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # If a dict is provided assume it's already JSON-serializable structure
        if isinstance(project_ir_or_data, dict):
            data = project_ir_or_data
        else:
            # Pydantic → dict
            data = project_ir_or_data.model_dump()

        self.writer.write(
            path=str(path),
            data=data,
        )

        logger.info("IR written to %s", output_path)
