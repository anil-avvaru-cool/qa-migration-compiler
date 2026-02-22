import logging
from typing import Dict, List, Any

from src.ast.models import ASTTree, ASTNode
from src.extraction.page_object_extractor import PageObjectExtractor
from src.extraction.locator_extractor import LocatorExtractor
from src.extraction.assertion_mapper import AssertionMapper
from src.extraction.action_mapper import ActionMapper


logger = logging.getLogger(__name__)


class IRExtractor:
    """
    Extraction layer.

    Responsible for:
    - Traversing AST
    - Extracting domain-level structures

    MUST NOT:
    - Build IR models
    - Generate IDs
    - Perform validation
    """

    def __init__(self):
        self.page_extractor = PageObjectExtractor()
        self.locator_extractor = LocatorExtractor()
        self.assertion_mapper = AssertionMapper()
        self.action_mapper = ActionMapper()

    def extract(
        self,
        ast_tree: ASTTree,
        project_name: str,
        source_language: str,
    ) -> Dict[str, Any]:

        logger.info("Starting extraction for project: %s", project_name)

        extracted_tests: List[Dict] = []
        extracted_suites: List[Dict] = []

        # --- Extract targets via dedicated extractors ---
        extracted_targets = []
        extracted_targets.extend(self.page_extractor.extract(ast_tree))
        extracted_targets.extend(self.locator_extractor.extract(ast_tree))

        # --- Traverse AST generically ---
        for node in self._traverse(ast_tree.root):

            if node.type == "test":
                extracted_test = self._extract_test(node)
                logger.debug(f"Extracted test***: {extracted_test}")
                extracted_tests.append(extracted_test)

            elif node.type == "suite":
                extracted_suites.append(self._extract_suite(node))

        extracted_project = {
            "project_name": project_name,
            "source_language": source_language,
            "tests": extracted_tests,
            "suites": extracted_suites,
            "targets": extracted_targets,
            "environments": [],
        }

        logger.info("Extraction complete for project: %s", project_name)
        return extracted_project

    # ------------------------
    # Internal helpers
    # ------------------------

    def _traverse(self, node: ASTNode):
        yield node
        for child in getattr(node, "children", []):
            yield from self._traverse(child)

    def _extract_test(self, node: ASTNode) -> Dict:

        steps: List[Dict] = []

        for statement in getattr(node, "children", []):
            action = self.action_mapper.map(statement)
            if action:
                steps.append(action)
                continue

            assertion = self.assertion_mapper.map(statement)
            if assertion:
                steps.append(assertion)

        return {
            "name": node.name,
            "steps": steps,
            "tags": getattr(node, "tags", []),
            "environment_id": getattr(node, "environment", None),
            "data_id": None,
        }

    def _extract_suite(self, node: ASTNode) -> Dict:
        test_names = [
            child.name
            for child in getattr(node, "children", [])
            if child.type == "test"
        ]

        return {
            "name": node.name,
            "tests": test_names,
            "parent_id": getattr(node, "parent", None),
        }
