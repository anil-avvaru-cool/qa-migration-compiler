import logging
from typing import Dict, List, Any

from src.ast.models import ASTTree, ASTNode
from src.extraction.page_object_extractor import PageObjectExtractor
from src.extraction.locator_extractor import LocatorExtractor
from src.extraction.assertion_mapper import AssertionMapper
from src.extraction.action_mapper import ActionMapper
from src.analysis.symbol_table import SymbolTable


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
        self.action_mapper = ActionMapper()  # Default with no symbol table
        self.symbol_table = SymbolTable()  # Will be built per AST tree

        # Optional cross-file analysis helpers (populated by pipeline when available)
        self.cross_index = None
        self.type_resolver = None
        self.call_graph = None
        self.data_flow = None
        self.wrapper_expander = None

    def extract(
        self,
        ast_tree: ASTTree,
        project_name: str,
        source_language: str,
    ) -> Dict[str, Any]:

        logger.info("Starting extraction for project: %s", project_name)

        # If a shared symbol_table was injected by the pipeline, reuse it.
        # Otherwise build a fresh one for this tree and attach available helpers.
        if getattr(self, "symbol_table", None) is None:
            self.symbol_table = SymbolTable(
                cross_index=self.cross_index,
                data_flow=self.data_flow,
                type_resolver=self.type_resolver,
            )

        # Ensure the symbol table is aware of cross-file helpers
        try:
            # assign helpers if symbol_table supports them
            self.symbol_table.cross_index = self.cross_index
            self.symbol_table.data_flow = self.data_flow
            self.symbol_table.type_resolver = self.type_resolver
        except Exception:
            pass

        # Build/update symbol table from the current tree (may augment existing)
        logger.info("Using symbol_table instance id=%s type=%s", id(self.symbol_table), f"{type(self.symbol_table).__module__}.{type(self.symbol_table).__name__}")
        self.symbol_table.build_from_tree(ast_tree)

        # Ensure ActionMapper uses the updated symbol table
        self.action_mapper = ActionMapper(symbol_table=self.symbol_table)

        extracted_tests: List[Dict] = []
        extracted_suites: List[Dict] = []
        extracted_pages: List[Dict] = []

        page_extractor = self.page_extractor.extract(ast_tree)
        logger.debug(f"Extracted page objects: {page_extractor}")
        extracted_pages.extend(page_extractor)

        # --- Extract targets via dedicated extractors ---
        extracted_targets = []
        
        locator_extractor = self.locator_extractor.extract(ast_tree)
        logger.debug(f"Extracted locators: {locator_extractor}")
        extracted_targets.extend(locator_extractor)

        # --- Traverse AST generically ---
        for node in self._traverse(ast_tree.root):

            if node.type == "test":
                extracted_test = self._extract_test(node)
                logger.debug(f"Extracted test: {extracted_test}")
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
            actions = self.action_mapper.map(statement)
            if actions:
                # action mapper returns a list of step dicts
                steps.extend(actions)
                continue

            assertions = self.assertion_mapper.map(statement)
            if assertions:
                steps.extend(assertions)

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
