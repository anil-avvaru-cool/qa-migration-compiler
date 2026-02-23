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

        # Build node map for parent traversal
        node_map = {n.id: n for n in self._walk(ast_tree.root)}

        for node in node_map.values():
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

                    # Try to find a variable/field name that holds this locator
                    variable_name = None
                    parent_id = node.parent_id
                    while parent_id:
                        parent = node_map.get(parent_id)
                        if not parent:
                            break
                        # Some parent nodes (variable declarator / field) contain a 'name'
                        candidate_name = parent.properties.get("name")
                        if candidate_name:
                            variable_name = candidate_name
                            break
                        parent_id = parent.parent_id

                    locators.append({
                        "id": node.id,
                        "name": variable_name,
                        "strategy": member,
                        "locator": value,
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
