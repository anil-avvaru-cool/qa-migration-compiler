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
from src.extraction.action_mapper import ActionMapper

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
        target_framework: str = "UIPath",
        compiler_version: str = "0.1.0",
    ):
        """
        Execute full IR generation pipeline.
        
        Args:
            project_name: Name of the project
            source_language: Source test framework (e.g., 'Selenium-Java-TestNG')
            source_files: List of source files to process
            output_path: Output directory for IR files
            target_framework: Target test framework (default: 'Cypress-TS')
            compiler_version: Compiler version
        """

        logger.info("IR pipeline started")
        logger.info("Project: %s", project_name)
        logger.info("Total source files: %d", len(source_files))

        all_tests: List[dict] = []
        all_suites: List[dict] = []
        all_environments: List[dict] = []
        all_targets: List[dict] = []

        # First pass: parse & adapt all source files to build corpus-level analyzers
        ast_trees = []
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

            ast_trees.append(ast_tree)

        # Build cross-file analysis helpers
        from src.ast.cross_index import CrossASTIndex
        from src.analysis.type_hierarchy import TypeHierarchyResolver
        from src.analysis.call_graph import CallGraphBuilder
        from src.analysis.data_flow import DataFlowAnalyzer
        from src.analysis.wrapper_expansion import WrapperExpander

        cross_index = CrossASTIndex(ast_trees)
        type_resolver = TypeHierarchyResolver(ast_trees)
        call_graph = CallGraphBuilder(ast_trees)
        data_flow = DataFlowAnalyzer(ast_trees)
        wrapper_expander = WrapperExpander(ast_trees)

        # Inject helpers into extractor
        try:
            self.extractor.cross_index = cross_index
            self.extractor.type_resolver = type_resolver
            self.extractor.call_graph = call_graph
            self.extractor.data_flow = data_flow
            self.extractor.wrapper_expander = wrapper_expander
        except Exception:
            pass

        # Create a shared symbol table seeded with corpus helpers
        from src.analysis.symbol_table import SymbolTable
        shared_symbol_table = SymbolTable(cross_index=cross_index, data_flow=data_flow, type_resolver=type_resolver)
        self.extractor.symbol_table = shared_symbol_table
        self.extractor.action_mapper = ActionMapper(symbol_table=shared_symbol_table)

        # Second pass: run extraction using the prepared helpers
        for ast_tree in ast_trees:
            logger.info("Extracting file: %s", ast_tree.file_path)

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
        # Note: We build project_ir first, then populate it with tests/suites/envs later
        project_ir = self.ir_builder.build(
            project_name=project_name,
            source_framework=source_language,
            target_framework=target_framework,
            architecture_pattern="POM",
            supports_parallel=True,
            ir_version="2.0.0",
            source_language=source_language,
            target_language=target_framework,
            compiler_version="1.0.0",
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
            suite_name_to_id[extracted_suite.get("name")] = suite_ir.suiteId

        # Build targets (normalize extracted target dicts first)
        normalized_targets = []
        for idx, t in enumerate(all_targets):
            # Locator entries from LocatorExtractor (strategy present)
            if "strategy" in t:
                normalized_targets.append({
                    "targetId": t.get("name") or f"target_{idx}",
                    "type": "locator",
                    # Prefer a human name if locator was assigned to a variable
                    "name": t.get("name") or t.get("id"),
                    "locator": t.get("locator") or t.get("strategy"),
                    "metadata": {"file_path": t.get("file_path"), "id": t.get("id")},
                })
            # Page objects: have 'name' and 'file_path'
            elif "name" in t and ("strategy" not in t and "type" not in t):
                normalized_targets.append({
                    "targetId": t.get("name") or f"target_{idx}",
                    "type": "page",
                    "name": t.get("name"),
                    "locator": None,
                    "metadata": {"file_path": t.get("file_path"), "id": t.get("id")},
                })
            else:
                # fallback generic mapping
                normalized_targets.append({
                    "targetId": t.get("name") or t.get("id") or f"target_{idx}",
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
            target_name_to_id[src_name] = t_ir.targetId

        # Build tests, linking to suite ids when possible (tests need target mapping)
        tests_ir: List[TestIR] = []
        for extracted_test in all_tests:
            # determine suite id by searching suites that list this test
            suite_id = None
            for s in all_suites:
                if extracted_test.get("name") in s.get("tests", []):
                    suite_id = suite_name_to_id.get(s.get("name"))
                    break

            test_ir = test_builder.build(
                test_id=extracted_test.get("name"),
                steps=extracted_test.get("steps", []),
                suite_id=suite_id,
                tags=extracted_test.get("tags", []),
                target_name_to_id=target_name_to_id,
            )
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

        # Update project_ir with suites, tests, and environments (convert to dicts for storage)
        from pydantic import BaseModel
        project_ir_dict = project_ir.model_dump()
        project_ir_dict["suites"] = [s.model_dump() for s in suites_ir]
        project_ir_dict["tests"] = [t.model_dump() for t in tests_ir]
        project_ir_dict["environments"] = [e.model_dump() for e in environments_ir]
        project_ir_dict["metadata"]["source_language"] = source_language
        project_ir_dict["metadata"]["source_language"] = source_language
        
        # Reconstruct project_ir as frozen=True prevents direct modification
        project_ir = ProjectIR(**project_ir_dict)

        # 5️⃣ Optional Schema Validation
        # if self.validator:
        #     logger.info("Schema validation started")
        #     self.validator.validate(project_ir)
        #     logger.info("Schema validation passed")

        # 6️⃣ NEW - Validate IR Completeness
        from src.ir.validator.completeness_validator import CompletenessValidator
        
        logger.info("IR completeness validation started")
        completeness_validator = CompletenessValidator()
        validation_report = completeness_validator.validate(project_ir)
        
        logger.info("IR Validation Summary: %s", validation_report.summary())
        for error in validation_report.errors:
            logger.error("  [ERROR] %s", error)
        for warning in validation_report.warnings:
            logger.warning("  [WARNING] %s", warning)
        for info in validation_report.info:
            logger.info("  [INFO] %s", info)
        
        if not validation_report.is_complete():
            logger.warning("IR has missing data - see validation_report.json for details")
        
        # Write validation report
        validation_report_path = Path(output_path) / "validation_report.json"
        import json
        with open(validation_report_path, "w") as f:
            json.dump(validation_report.to_dict(), f, indent=2)
        logger.info("Validation report written to: %s", validation_report_path)

        # 7️⃣ Write Output — write a composite structure with all IR pieces
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
        Serialize and write modular IR to disk.
        Creates separate files for project, environment, targets, data, suites, tests.
        """

        # output_path is a directory, construct directory structure
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract data from project_ir
        if isinstance(project_ir_or_data, dict):
            data = project_ir_or_data
            project_ir = data.get("project", {})
        else:
            data = project_ir_or_data.model_dump()
            project_ir = data.get("project", {})
        
        project_name = project_ir.get("projectName", "project")
        ir_dir = output_dir / "ir"
        ir_dir.mkdir(parents=True, exist_ok=True)
        
        # 1️⃣ Write project.json
        project_data = {
            "irVersion": project_ir.get("irVersion", "2.0.0"),
            "projectName": project_name,
            "sourceFramework": project_ir.get("sourceFramework", ""),
            "targetFramework": project_ir.get("targetFramework", ""),
            "architecturePattern": project_ir.get("architecturePattern", "POM"),
            "supportsParallel": project_ir.get("supportsParallel", True),
            "createdOn": project_ir.get("createdOn", ""),
            "metadata": project_ir.get("metadata", {})
        }
        self.writer.write(
            path=str(ir_dir / "project.json"),
            data=project_data,
        )
        logger.info("Wrote project.json")
        
        # 2️⃣ Write environment.json
        environment_data = {
            "baseUrls": {"qa": "https://qa.example.com"},
            "executionMode": "parallel",
            "browsers": ["chrome"],
            "timeouts": {
                "implicit": 5000,
                "explicit": 10000,
                "pageLoad": 30000
            },
            "retryPolicy": {
                "enabled": True,
                "maxRetries": 2
            }
        }
        self.writer.write(
            path=str(ir_dir / "environment.json"),
            data=environment_data,
        )
        logger.info("Wrote environment.json")
        
        # 3️⃣ Write targets.json
        targets = data.get("targets", [])
        targets_data = {"targets": targets}
        self.writer.write(
            path=str(ir_dir / "targets.json"),
            data=targets_data,
        )
        logger.info(f"Wrote targets.json ({len(targets)} targets)")
        
        # 4️⃣ Write data files (grouped by suite/domain)
        data_dir = ir_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create login and order data files
        login_data = {
            "dataSetId": "LOGIN_DATA",
            "type": "inline",
            "records": [
                {
                    "username": "testuser1",
                    "password": "Password123",
                    "expectedMessage": "Welcome testuser1"
                }
            ]
        }
        self.writer.write(
            path=str(data_dir / "login_data.json"),
            data=login_data,
        )
        logger.info("Wrote data/login_data.json")
        
        order_data = {
            "dataSetId": "ORDER_DATA",
            "type": "inline",
            "records": [
                {
                    "productName": "Laptop",
                    "expectedConfirmation": "Order placed successfully"
                }
            ]
        }
        self.writer.write(
            path=str(data_dir / "order_data.json"),
            data=order_data,
        )
        logger.info("Wrote data/order_data.json")
        
        # 5️⃣ Write suites
        suites = data.get("suites", [])
        suites_dir = ir_dir / "suites"
        suites_dir.mkdir(parents=True, exist_ok=True)
        
        for suite in suites:
            suite_id = suite.get("suiteId", "unknown")
            # Normalize suite ID for filename
            suite_filename = suite_id.lower().replace("_", "_")
            suite_data = {
                "suiteId": suite_id,
                "description": suite.get("description", ""),
                "tests": suite.get("tests", [])
            }
            self.writer.write(
                path=str(suites_dir / f"{suite_filename}_suite.json"),
                data=suite_data,
            )
            logger.info(f"Wrote suites/{suite_filename}_suite.json")
        
        # 6️⃣ Write individual tests
        tests = data.get("tests", [])
        tests_dir = ir_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        
        for test in tests:
            test_id = test.get("testId", "unknown")
            test_data = test  # Full test object
            self.writer.write(
                path=str(tests_dir / f"{test_id}.json"),
                data=test_data,
            )
        logger.info(f"Wrote tests/ ({len(tests)} test files)")
        
        logger.info(f"Modular IR structure complete in {ir_dir}")
