# src/extraction/locator_extractor.py

import logging
from typing import List, Dict
from src.ast.models import ASTTree, ASTNode


logger = logging.getLogger(__name__)


class LocatorExtractor:
    """
    Extract Selenium By.* locators (MVP).
    """

    def extract(self, ast_tree: ASTTree) -> List[Dict]:
        logger.info("Locator extraction started")

        locators: List[Dict] = []

        for node in self._walk(ast_tree.root):
            if node.type == "MethodInvocation":
                qualifier = node.properties.get("qualifier")
                member = node.properties.get("member")

                if qualifier == "By":
                    locators.append({
                        "id": node.id,
                        "strategy": member,
                        "file_path": ast_tree.file_path,
                    })

        logger.info("Locator extraction completed")
        return locators

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)
