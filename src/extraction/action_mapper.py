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
    
    LEVEL 1: Direct Selenium calls (sendKeys, click, get, etc.)
    LEVEL 2: Page object method calls -> resolved to method definition -> extract internal actions
    LEVEL 3: Parameter mapping from call site to method parameters
    """

    def __init__(self, symbol_table: Optional[SymbolTable] = None):
        self.symbol_table = symbol_table
        self.call_graph = None  # Will be injected by pipeline
        self.data_flow = None  # Will be injected by pipeline

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
            is_page_object_call = self._is_page_object_method(qualifier, member)

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

            # NEW: LEVEL 2 - Try to follow page object method calls
            if is_page_object_call and self.call_graph:
                try:
                    class_name = qualifier
                    method_def = self.call_graph.resolve_method_definition(class_name, member)
                    
                    if method_def:
                        logger.debug("[ActionMapper] Level 2: Following page object call %s.%s()", class_name, member)
                        
                        # Extract actions from method body
                        internal_actions = self.extract_from_method_body(
                            method_def, node, class_name, member
                        )
                        actions.extend(internal_actions)
                        
                        # Store the method context for enricher
                        step_obj["page_class"] = class_name
                        step_obj["method_name"] = member
                except Exception as e:
                    logger.debug("[ActionMapper] Level 2 extraction failed: %s", e)

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
    # NEW METHODS FOR WEEK 2: Multi-Level Analysis
    
    def _is_page_object_method(self, qualifier: Optional[str], member: Optional[str]) -> bool:
        """
        Check if this is a page object method call.
        
        Page object methods are calls to methods on page object instances.
        Examples: productPage.navigateToProducts(), loginPage.enterUsername()
        """
        if not qualifier or not member:
            return False
        
        # Page object qualifiers don't match known Selenium classes
        non_page_object_qualifiers = {
            "Duration", "ExpectedConditions", "By", "", "driver", "wait", 
            "WebDriver", "WebElement", "Actions", "js", "jsExecutor"
        }
        
        return qualifier not in non_page_object_qualifiers and member not in UTILITY_METHODS

    def extract_from_method_body(
        self,
        method_def: ASTNode,
        call_node: ASTNode,
        class_name: str,
        method_name: str
    ) -> List[Dict]:
        """
        LEVEL 2: Extract actions from method implementation.
        
        Given a page object method definition, walk its body and extract
        all Selenium actions found inside.
        """
        internal_actions = []
        
        if not method_def or not hasattr(method_def, 'children'):
            return internal_actions
        
        logger.debug("[ActionMapper] Extracting Level 2 actions from %s.%s()", class_name, method_name)
        
        # Walk method body statements
        for stmt in method_def.children:
            for node in self._walk(stmt):
                member = node.properties.get("member")
                
                if member and member not in UTILITY_METHODS:
                    # Check if it's a semantic action (Level 1)
                    action_type = self._infer_semantic_action_type(member, None)
                    
                    if action_type:
                        action = self._extract_direct_action(node)
                        
                        # LEVEL 3: Map parameters from call site
                        action = self._map_parameters_from_call_site(
                            action, call_node, method_def, method_name
                        )
                        
                        internal_actions.append(action)
                        logger.debug("[ActionMapper] Level 2 extracted action: %s", action.get("action"))
        
        return internal_actions

    def _map_parameters_from_call_site(
        self,
        action: Dict,
        call_node: ASTNode,
        method_def: ASTNode,
        method_name: str
    ) -> Dict:
        """
        LEVEL 3: Map call site arguments to method parameters.
        
        When a page object method is called with arguments, and we've extracted
        an action from inside the method that uses parameters, map the actual
        call arguments to the parameter usage.
        
        Example:
          Call site: productPage.searchProduct("Laptop")
          Method body: typeText(searchInput, productName)
          We map: productName -> "Laptop"
        """
        if not action.get("input"):
            return action
        
        logger.debug("[ActionMapper] Using DataFlow to map parameters for %s", method_name)
        
        # Extract call arguments
        call_args = self._extract_call_arguments(call_node)
        
        # Extract method parameters
        method_params = self._extract_method_parameters(method_def)
        
        if not call_args or not method_params:
            return action
        
        # Build mapping: parameter_name -> call_argument_value
        param_mapping = {}
        for call_arg, method_param in zip(call_args, method_params):
            param_name = method_param.properties.get("name") if hasattr(method_param, 'properties') else None
            arg_value = self._extract_argument_value(call_arg)
            
            if param_name and arg_value is not None:
                param_mapping[param_name] = arg_value
                logger.debug("[ActionMapper] Parameter mapping: %s -> %s", param_name, arg_value)
        
        # Apply mapping to action input
        if action.get("input") and param_mapping:
            input_field = action["input"].get("field")
            if input_field and input_field in param_mapping:
                action["input"]["value"] = param_mapping[input_field]
                action["input"]["source"] = "call_argument"
                logger.debug("[ActionMapper] Mapped input: %s=%s", input_field, param_mapping[input_field])
        
        return action

    def _extract_call_arguments(self, call_node: ASTNode) -> List[ASTNode]:
        """Extract argument nodes from a method call."""
        arguments = []
        if hasattr(call_node, 'children'):
            for child in call_node.children:
                if child.type in ("argument", "literal", "variable", "methodInvocation", "value"):
                    arguments.append(child)
        return arguments

    def _extract_method_parameters(self, method_def: ASTNode) -> List[ASTNode]:
        """Extract parameter nodes from a method definition."""
        parameters = []
        if hasattr(method_def, 'children'):
            for child in method_def.children:
                if child.type == "parameter":
                    parameters.append(child)
        return parameters

    def _extract_argument_value(self, arg_node: ASTNode) -> Optional[str]:
        """Extract the actual value from an argument node."""
        if arg_node.type == "literal":
            value = arg_node.properties.get("value")
            # Remove quotes if present
            if value and isinstance(value, str):
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    return value[1:-1]
            return value
        elif arg_node.type == "variable":
            return arg_node.properties.get("name")
        elif arg_node.type == "methodInvocation":
            return arg_node.properties.get("member")
        else:
            return None