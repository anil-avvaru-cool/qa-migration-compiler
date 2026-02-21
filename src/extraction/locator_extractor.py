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
        seen_selectors = {}  # Track first occurrence of each selector

        for node in self._walk(ast_tree.root):
            qualifier = node.properties.get("qualifier")
            member = node.properties.get("member")
            value = node.properties.get("value", "")

            if qualifier == "By" and member:
                # Create key to track unique selectors
                selector_key = (member, value)
                
                if selector_key not in seen_selectors:
                    seen_selectors[selector_key] = 0
                
                # Only keep first occurrence of each unique selector
                if seen_selectors[selector_key] == 0:
                    locators.append({
                        "id": node.id,
                        "strategy": member,
                        "file_path": ast_tree.file_path,
                    })
                seen_selectors[selector_key] += 1

        logger.info("Locator extraction completed")
        return locators

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)
