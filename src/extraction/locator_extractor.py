# src/extraction/locator_extractor.py

import logging
import re
from typing import List, Dict, Optional
from src.ast.models import ASTTree, ASTNode


logger = logging.getLogger(__name__)

# Semantic role inference patterns
ROLE_PATTERNS = {
    "textbox": [r"input\[type=(text|password|email|search)\]", r"input(?!.*submit)", r"textarea"],
    "button": [r"button", r"input\[type=submit\]", r"input\[type=button\]", r"\[onclick\]"],
    "label": [r"label", r"span.*text", r"p.*text"],
    "checkbox": [r"input\[type=checkbox\]"],
    "radio": [r"input\[type=radio\]"],
    "select": [r"select"],
}

# Business name patterns
BUSINESSNAME_PATTERNS = {
    "textbox": [r"Input$", r"Field$", r"TextBox$", r"Search$"],
    "button": [r"Button$", r"Btn$", r"Click$", r"Submit$"],
    "label": [r"Label$", r"Text$", r"Message$", r"Display$"],
    "checkbox": [r"Check$", r"Checkbox$", r"Toggle$"],
    "radio": [r"Radio$", r"Option$"],
    "select": [r"Dropdown$", r"Select$"],
}


class LocatorExtractor:
    """
    Enhanced Locator Extractor with page context and semantic role inference.
    
    Responsibilities:
    - Extract Selenium By.* locators
    - Extract page context (which class contains the locator)
    - Infer semantic role (textbox, button, label, etc.)
    - Normalize selector values (remove extra quotes)
    - Support multiple selector strategies
    """

    def extract(self, ast_tree: ASTTree) -> List[Dict]:
        """Extract locators with context and semantic information."""
        logger.info("Enhanced locator extraction started for %s", ast_tree.file_path)
        locators: List[Dict] = []
        seen_locators = set()

        # Build node map for traversal
        node_map = {n.id: n for n in self._walk(ast_tree.root)}

        # Extract page class name from file path or class declaration
        page_class = self._extract_page_class(ast_tree, node_map)

        for node in node_map.values():
            qualifier = node.properties.get("qualifier")
            member = node.properties.get("member")

            if qualifier == "By" and member:
                # Get normalized selector value
                raw_value = self._extract_selector_value(node)
                normalized_value = self._normalize_selector_value(raw_value)

                if not normalized_value:
                    continue

                # Create unique key
                locator_key = (member, normalized_value, page_class)

                if locator_key not in seen_locators:
                    seen_locators.add(locator_key)

                    # Extract variable name
                    variable_name = self._find_variable_name(node, node_map)

                    # Infer semantic role and business name
                    semantic_role = self._infer_semantic_role(normalized_value, variable_name)
                    business_name = variable_name or f"element_{semantic_role}"

                    # Create comprehensive locator object
                    locators.append({
                        "id": node.id,
                        "strategy": member,
                        "targetId": self._generate_target_id(variable_name, page_class),
                        "name": variable_name,
                        "type": "ui-element",
                        "context": {
                            "page": page_class,
                        },
                        "semantic": {
                            "role": semantic_role,
                            "businessName": business_name,
                        },
                        "selectorStrategies": [
                            {
                                "strategy": self._map_strategy(member),
                                "value": normalized_value,
                                "stabilityScore": self._estimate_stability(normalized_value, member),
                            },
                            # Add alternative strategies if applicable
                            *self._generate_alternative_strategies(normalized_value, member),
                        ],
                        "preferredStrategy": self._map_strategy(member),
                        "file_path": ast_tree.file_path,
                    })

        logger.info("Enhanced locator extraction completed: %d locators found", len(locators))
        return locators

    def _extract_page_class(self, ast_tree: ASTTree, node_map: Dict) -> Optional[str]:
        """Extract page class name from AST root or file path."""
        # Try to find class declaration in root
        for node in node_map.values():
            if node.type == "class":
                class_name = node.properties.get("name")
                if class_name and ("Page" in class_name or "Test" in class_name):
                    return class_name

        # Fallback: extract from file path
        file_path = ast_tree.file_path
        if file_path and "/" in file_path:
            filename = file_path.split("/")[-1].replace(".java", "")
            return filename
        return None

    def _extract_selector_value(self, node: ASTNode) -> str:
        """Extract selector value from method arguments."""
        for child in node.children:
            value = child.properties.get("value", "")
            if value:
                return value
        return ""

    def _normalize_selector_value(self, value: str) -> str:
        """Remove extra quotes and clean up selector values."""
        if not value:
            return ""

        # Remove wrapping quotes if present
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        # Remove escaped quotes inside
        value = value.replace('\\"', '"').replace("\\'", "'")
        value = value.strip()

        return value

    def _find_variable_name(self, node: ASTNode, node_map: Dict) -> Optional[str]:
        """Find the variable/field name that holds this locator."""
        parent_id = node.parent_id
        depth = 0
        max_depth = 5

        while parent_id and depth < max_depth:
            parent = node_map.get(parent_id)
            if not parent:
                break

            candidate_name = parent.properties.get("name")
            if candidate_name and candidate_name not in ("By", "driver", "wait"):
                return candidate_name

            parent_id = parent.parent_id
            depth += 1

        return None

    def _infer_semantic_role(self, selector: str, variable_name: Optional[str]) -> str:
        """Infer semantic role from selector pattern and/or variable name."""
        selector_lower = selector.lower()
        name_lower = (variable_name or "").lower()

        # Check business name patterns first (higher priority)
        for role, patterns in BUSINESSNAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    return role

        # Check selector patterns
        for role, patterns in ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, selector_lower, re.IGNORECASE):
                    return role

        # Fallback
        return "element"

    def _generate_target_id(self, variable_name: Optional[str], page_class: Optional[str]) -> str:
        """Generate a target ID in UPPERCASE style."""
        if variable_name:
            # Convert camelCase to SNAKE_CASE
            target_id = re.sub(r'(?<!^)(?=[A-Z])', '_', variable_name).upper()
        else:
            target_id = page_class or "ELEMENT"

        return target_id

    def _map_strategy(self, by_method: str) -> str:
        """Map Selenium By.* method to strategy name."""
        mapping = {
            "id": "css",
            "name": "css",
            "className": "css",
            "tagName": "css",
            "cssSelector": "css",
            "xpath": "xpath",
            "linkText": "xpath",
            "partialLinkText": "xpath",
        }
        return mapping.get(by_method, "css")

    def _estimate_stability(self, selector: str, strategy: str) -> float:
        """Estimate selector stability score (0.0 - 1.0)."""
        score = 0.85

        # XPath penalties
        if strategy == "xpath":
            score -= 0.05  # XPath slightly less stable than CSS
            if "//" in selector:
                score -= 0.05  # Absolute XPath less stable
            if "contains(" in selector.lower():
                score -= 0.05  # String matching less stable

        # CSS selector bonuses
        if strategy == "cssSelector":
            if selector.startswith("#"):
                score = 0.96  # ID selector most stable
            elif selector.startswith("."):
                score = 0.90  # Class selector stable

        # By.id and By.name (mapped to CSS)
        if strategy in ("id", "name"):
            score = 0.97  # Very stable

        return min(1.0, max(0.0, score))

    def _generate_alternative_strategies(self, selector: str, by_method: str) -> List[Dict]:
        """Generate alternative selector strategies for cross-framework support."""
        alternatives = []

        # Try to generate XPath alternative for CSS selectors
        if by_method in ("cssSelector", "id", "name", "className"):
            xpath_alt = self._css_to_xpath(selector)
            if xpath_alt and xpath_alt != selector:
                alternatives.append({
                    "strategy": "xpath",
                    "value": xpath_alt,
                    "stabilityScore": 0.85,
                })

        # Add UiPath strategy hint for cross-framework support
        if by_method == "id":
            alternatives.append({
                "strategy": "uipath-selector",
                "value": f"<webctrl id='{selector}' />",
                "stabilityScore": 0.88,
            })

        return alternatives

    def _css_to_xpath(self, css_selector: str) -> Optional[str]:
        """Convert simple CSS selector to XPath (best effort)."""
        try:
            # Handle simple CSS selectors
            if css_selector.startswith("#"):
                element_id = css_selector[1:]
                return f"//*[@id='{element_id}']"
            elif css_selector.startswith("."):
                class_name = css_selector[1:]
                return f"//*[@class='{class_name}']"
            # More complex CSS selectors would need full CSS parser
            return None
        except Exception:
            return None

    def _walk(self, node: ASTNode):
        """Depth-first traversal of AST."""
        yield node
        for child in node.children:
            yield from self._walk(child)
