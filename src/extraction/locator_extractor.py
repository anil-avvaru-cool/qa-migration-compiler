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
        seen_locators = set()  # Track unique locators by (strategy, value)

        for node in self._walk(ast_tree.root):
            qualifier = node.properties.get("qualifier")
            member = node.properties.get("member")

            if qualifier == "By" and member:
                # Get the selector value from children (arguments)
                value = self._extract_selector_value(node)
                
                # Create unique key
                locator_key = (member, value)
                
                # Only keep first occurrence of each unique locator
                if locator_key not in seen_locators:
                    seen_locators.add(locator_key)
                    locators.append({
                        "id": node.id,
                        "strategy": member,
                        "file_path": ast_tree.file_path,
                    })

        logger.info("Locator extraction completed")
        return locators

    def _extract_selector_value(self, node: ASTNode) -> str:
        """Extract the selector value from method arguments (children)"""
        for child in node.children:
            value = child.properties.get("value", "")
            if value:
                return value
        return ""

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)
