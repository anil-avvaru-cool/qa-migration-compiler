# src/extraction/action_mapper.py

import logging
from typing import List, Dict, Optional
from src.ast.models import ASTTree, ASTNode
from src.analysis.symbol_table import SymbolTable


logger = logging.getLogger(__name__)


SUPPORTED_ACTIONS = {
    "click",
    "sendKeys",
    "submit",
    "clear",
    "doubleClick",
    "contextClick",
    "getText",
    "waitForVisible",
    "navigate",
}

# Utility methods that shouldn't be treated as test steps
UTILITY_METHODS = {
    "findElement",
    "findElements",
    "manage",
    "timeouts",
    "implicitlyWait",
    "until",
    "get",
    "presenceOfElementLocated",
    "visibilityOfElementLocated",
    "elementToBeClickable",
}


class ActionMapper:
    """
    Extract Selenium interaction methods.
    Uses symbol table for robust target resolution.
    """

    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        self.symbol_table = symbol_table

    def map(self, ast_node: ASTNode) -> List[Dict]:
        logger.info("Action mapping started")

        actions: List[Dict] = []

        for node in self._walk(ast_node):
            member = node.properties.get("member")
            qualifier = node.properties.get("qualifier")

            if not member or member in UTILITY_METHODS:
                continue

            # Match either:
            # 1. Direct Selenium actions (click, sendKeys, etc.)
            # 2. Method calls on page objects (where qualifier is set to an object, e.g., loginPage.enterEmail)
            is_selenium_action = member in SUPPORTED_ACTIONS
            is_page_object_call = qualifier and qualifier not in ("Duration", "ExpectedConditions", "By", "", "driver", "wait")
            
            if not (is_selenium_action or is_page_object_call):
                continue

            # Use symbol table for robust target resolution if available
            target_name_id = None
            target_node_id = None

            if self.symbol_table:
                result = self.symbol_table.resolve_step_target(node)
                if result:
                    target_name_id, target_node_id = result
            else:
                # Fallback: best-effort local resolution
                target_node_id = self._find_target(node)

            parameters = self._extract_parameters(node)

            actions.append({
                "type": "action",
                "name": member,
                "target_name_id": target_name_id,
                "target_node_id": target_node_id,
                "parameters": parameters,
            })

        logger.info("Action mapping completed")
        return actions

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)

    def _extract_parameters(self, node: ASTNode):
        """Extract simple parameters (e.g., sendKeys text) from node children."""
        params = {}
        # Look for literal value among children
        for child in node.children:
            val = child.properties.get("value")
            if val:
                params["value"] = val
                break
        return params

    def _find_target(self, node: ASTNode):
        """Best-effort search for a related locator or reference name in the node subtree."""
        # Prefer a descendant that is a By.* invocation
        for n in self._walk(node):
            qualifier = n.properties.get("qualifier")
            member = n.properties.get("member")
            if qualifier == "By" and member:
                return n.id

        # Fall back to a referenced variable/member name in arguments
        for n in self._walk(node):
            mem = n.properties.get("member")
            name = n.properties.get("name")
            if mem and not mem in SUPPORTED_ACTIONS:
                return mem
            if name:
                return name

        # As last resort return the node id
        return node.id
