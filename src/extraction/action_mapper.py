# src/extraction/action_mapper.py

import logging
import re
from typing import List, Dict, Optional
from src.ast.models import ASTTree, ASTNode
from src.analysis.symbol_table import SymbolTable


logger = logging.getLogger(__name__)

# Semantic action type mapping
SEMANTIC_ACTION_MAP = {
    # Click actions
    "click": "click",
    "doubleClick": "doubleClick",
    "contextClick": "rightClick",
    "submit": "submit",

    # Type/input actions
    "sendKeys": "type",
    "clear": "clear",
    "select": "select",

    # Navigation
    "get": "navigate",
    "navigate": "navigate",

    # Wait actions
    "waitForVisible": "waitForVisible",
    "wait": "wait",

    # Get/Read actions
    "getText": "getText",
    "getAttribute": "getAttribute",
    "getTagName": "getTagName",
    "getCssValue": "getCssValue",
}

# Page object method naming patterns to infer action types
PAGE_OBJECT_ACTION_PATTERNS = {
    "enter.*": "type",
    "type.*": "type",
    "fill.*": "type",
    "set.*": "type",
    "click.*": "click",
    "select.*": "select",
    "choose.*": "select",
    "submit.*": "submit",
    "check.*": "click",
    "uncheck.*": "click",
    "navigate.*": "navigate",
    "go.*": "navigate",
    "wait.*": "waitForVisible",
}

# Utility methods that shouldn't be treated as test steps
UTILITY_METHODS = {
    "findElement",
    "findElements",
    "manage",
    "timeouts",
    "implicitlyWait",
    "until",
    "presenceOfElementLocated",
    "visibilityOfElementLocated",
    "elementToBeClickable",
}


class ActionMapper:
    """
    Enhanced Action Mapper with semantic action type inference.
    
    Maps Selenium interactions to semantic action types (navigate, type, click, etc.)
    Supports both direct Selenium actions and page object methods.
    """

    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        self.symbol_table = symbol_table

    def map(self, ast_node: ASTNode) -> List[Dict]:
        """Map AST node to list of action steps."""
        logger.info("Enhanced action mapping started")

        actions: List[Dict] = []

        for node in self._walk(ast_node):
            member = node.properties.get("member")
            qualifier = node.properties.get("qualifier")

            if not member or member in UTILITY_METHODS:
                continue

            # Check if it's a semantic action
            is_semantic_action = member in SEMANTIC_ACTION_MAP
            is_page_object_call = qualifier and qualifier not in (
                "Duration", "ExpectedConditions", "By", "", "driver", "wait", "WebDriver"
            )

            if not (is_semantic_action or is_page_object_call):
                continue

            # Map to semantic action type
            action_type = self._infer_semantic_action_type(member, qualifier)

            if not action_type:
                continue

            # Resolve target information
            target_name_id = None
            target_id = None

            # Prefer symbol table resolution when available
            if self.symbol_table:
                result = self.symbol_table.resolve_step_target(node)
                if result:
                    target_name_id, target_id = result
            else:
                # Try find direct locator/member reference
                target_ref = self._find_target_reference(node)
                if target_ref:
                    # If we found a By.* locator child, leave resolution to enricher
                    target_name_id = target_ref

            # If call looks like a page-object method (enterUsername, clickLogin),
            # derive a probable target name from the method name to aid enricher.
            if is_page_object_call and member:
                # strip common verbs: enter, click, type, select, submit, get
                derived = re.sub(r'^(enter|click|type|select|choose|submit|get|set|fill|go|navigate|check|uncheck)', '', member, flags=re.IGNORECASE)
                # lower-first char variant
                if derived:
                    probable_name = derived[0].lower() + derived[1:] if len(derived) > 1 else derived.lower()
                    # prefer explicit name only if not already set
                    if not target_name_id:
                        target_name_id = probable_name

            # Extract input data source
            step_input = self._extract_step_input(node, member)

            # Extract target URL for navigate actions
            step_target = None
            if action_type == "navigate":
                step_target = self._extract_navigate_target(node)

            # Create step object (ensure consistent keys expected by enricher/builder)
            step_obj = {
                "type": "action",
                "action": action_type,
                "name": member,
                "stepId": None,  # Will be assigned by builder/enricher
                "targetId": target_id,
                "target_name_id": target_name_id,
                "target": step_target,
                "input": step_input,
                "parameters": self._extract_parameters(node, member),
            }

            logger.debug("Mapped AST node to step: %s", step_obj)
            actions.append(step_obj)

        logger.info("Enhanced action mapping completed: %d actions found", len(actions))
        return actions

    def _infer_semantic_action_type(self, method_name: str, qualifier: Optional[str]) -> Optional[str]:
        """Infer semantic action type from method name."""

        # First check direct Selenium action mapping
        if method_name in SEMANTIC_ACTION_MAP:
            return SEMANTIC_ACTION_MAP[method_name]

        # Then check page object method patterns
        method_lower = method_name.lower()
        for pattern, action_type in PAGE_OBJECT_ACTION_PATTERNS.items():
            if re.match(pattern, method_lower):
                return action_type

        # Special case: "get" on WebDriver context
        if method_name == "get" and qualifier in ("driver", "webDriver"):
            return "navigate"

        return None

    def _find_target_reference(self, node: ASTNode) -> Optional[str]:
        """Find target reference from node properties."""
        # Look for direct reference
        if node.properties.get("member") and node.properties.get("member") not in UTILITY_METHODS:
            return node.properties.get("member")

        # Look in children for By.* or variable references
        for child in self._walk(node):
            qualifier = child.properties.get("qualifier")
            member = child.properties.get("member")

            if qualifier == "By" and member:
                return None  # Locator found, will be linked by enricher

            if member and member not in UTILITY_METHODS:
                return member

        return None

    def _extract_step_input(self, node: ASTNode, method_name: str) -> Optional[Dict]:
        """Extract input data source from method arguments."""

        # Only certain actions have inputs
        if method_name not in ("sendKeys", "select", "clear"):
            return None

        # Look for literal value in children
        for child in self._walk(node):
            value = child.properties.get("value")
            if value:
                # This is a literal constant value
                return {
                    "source": "constant",
                    "value": value,
                }

            # Look for variable reference
            name = child.properties.get("name")
            if name:
                # Assume it comes from data source
                return {
                    "source": "data",
                    "field": name,
                }

        return None

    def _extract_navigate_target(self, node: ASTNode) -> Optional[Dict]:
        """Extract URL target from navigate action."""
        # Look for URL value in children
        for child in self._walk(node):
            value = child.properties.get("value")
            if value and ("http" in value.lower() or "qa:" in value.lower() or "/" in value):
                return {
                    "type": "url",
                    "value": value,
                }

        return None

    def _extract_parameters(self, node: ASTNode, method_name: str) -> Dict:
        """Extract additional parameters from node."""
        params = {}

        # For sendKeys, look for textual input
        if method_name == "sendKeys":
            for child in self._walk(node):
                value = child.properties.get("value")
                if value:
                    params["inputText"] = value
                    break

        # For wait actions, extract timeout if present
        if "wait" in method_name.lower():
            for child in self._walk(node):
                value = child.properties.get("value")
                if value and isinstance(value, (int, str)) and str(value).isdigit():
                    params["timeout"] = int(value)
                    break

        return params

    def _walk(self, node: ASTNode):
        """Depth-first traversal of AST."""
        yield node
        for child in node.children:
            yield from self._walk(child)
