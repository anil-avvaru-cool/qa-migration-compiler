"""
Data-flow analysis for locator binding.

Performs conservative propagation of locator initializers through assignments
and simple method returns using call graph information.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple, List
import logging

from src.ast.models import ASTTree, ASTNode
from src.analysis.call_graph import CallGraphBuilder
from src.analysis.type_hierarchy import TypeHierarchyResolver
from src.ast.cross_index import CrossASTIndex

logger = logging.getLogger(__name__)


class DataFlowAnalyzer:
    """Analyze locator/value flow to resolve effective initializer nodes."""

    def __init__(self, trees: List[ASTTree]):
        self.trees = trees
        self.cross_index = CrossASTIndex(trees)
        self.call_graph = CallGraphBuilder(trees)
        self.type_resolver = TypeHierarchyResolver(trees)

    def find_locator_for_symbol(self, symbol_name: str) -> Optional[ASTNode]:
        """Search across the corpus for a locator initializer for a symbol name.

        Conservative strategy:
        1. Find a field/variable node named symbol_name and return first locator descendant.
        2. If not found, search for methods that return this symbol (not implemented complexly).
        """
        for node in self.cross_index.by_type("field") + self.cross_index.by_type("variable"):
            if node.name == symbol_name:
                for descendant in node.walk():
                    qualifier = descendant.properties.get("qualifier")
                    member = descendant.properties.get("member")
                    if qualifier == "By" and member:
                        return descendant

        return None
    # NEW METHODS FOR WEEK 1: Parameter Mapping
    
    def get_parameter_mappings(
        self,
        call_node: ASTNode,
        method_def: ASTNode
    ) -> Dict[int, Dict]:
        """
        Map call site arguments to method parameter definitions.
        
        Args:
            call_node: ASTNode of the method call (e.g., searchProduct("Laptop"))
            method_def: ASTNode of the method definition (e.g., def searchProduct(String productName))
            
        Returns:
            Dict mapping parameter index to parameter info:
            {0: {"name": "productName", "type": "String", "value": "Laptop", "source": "literal"}}
            
        Example:
            # For: productPage.searchProduct("Laptop")
            # Mapping: {0: {"name": "productName", "value": "Laptop", "source": "literal"}}
        """
        mappings = {}
        
        # Get call arguments from the call node
        call_args = self._extract_call_arguments(call_node)
        
        # Get method parameters from the method definition
        method_params = self._extract_method_parameters(method_def)
        
        # Map each argument to its corresponding parameter
        for param_index, (call_arg, method_param) in enumerate(zip(call_args, method_params)):
            arg_value = self._extract_argument_value(call_arg)
            arg_source = self.classify_argument_type(call_arg)
            
            param_info = {
                "index": param_index,
                "name": method_param.get("name"),
                "type": method_param.get("type"),
                "value": arg_value,
                "source": arg_source,
            }
            
            mappings[param_index] = param_info
            logger.debug("[DataFlow] Parameter mapping [%d]: %s -> %s", 
                        param_index, method_param.get("name"), param_info)
        
        return mappings

    def get_variable_definitions(self, var_name: str, in_method: Optional[str] = None) -> List[Dict]:
        """
        Find all assignments to a variable.
        
        Args:
            var_name: Name of the variable to track
            in_method: Optional method name to limit scope
            
        Returns:
            List of definitions: [{"line": 15, "value": "testuser1", "type": "literal"}]
        """
        definitions = []
        
        # Search for variable assignments
        for node in self.cross_index.by_type("assignment"):
            if node.properties.get("target") == var_name:
                value = node.properties.get("value")
                value_type = self.classify_value_type(value)
                
                definition = {
                    "variable": var_name,
                    "value": value,
                    "type": value_type,
                    "node": node,
                }
                definitions.append(definition)
                logger.debug("[DataFlow] Found definition of %s: %s", var_name, value)
        
        return definitions

    def classify_argument_type(self, argument: ASTNode) -> str:
        """
        Classify the type of an argument.
        
        Returns: "literal" | "variable" | "method_call" | "field_access"
        """
        node_type = argument.type
        
        if node_type == "literal":
            return "literal"
        elif node_type == "variable":
            return "variable"
        elif node_type in ("methodInvocation", "call"):
            return "method_call"
        elif node_type == "fieldAccess":
            return "field_access"
        else:
            return "unknown"

    def classify_value_type(self, value: any) -> str:
        """Classify the type of a value."""
        if isinstance(value, str):
            if value.startswith('"') or value.startswith("'"):
                return "string_literal"
            return "string_variable"
        elif isinstance(value, (int, float)):
            return "numeric_literal"
        else:
            return "unknown"

    def trace_variable_origin(self, var_name: str, in_ast_node: ASTNode) -> Optional[Dict]:
        """
        Trace a variable back to its origin (assignment/parameter).
        
        Args:
            var_name: Name of the variable
            in_ast_node: AST node context for the lookup
            
        Returns:
            Dict with origin info: {"type": "literal", "value": "testuser1"}
        """
        # Try to find assignment in this scope
        definitions = self.get_variable_definitions(var_name)
        if definitions:
            origin = definitions[0]  # Take first definition
            logger.debug("[DataFlow] Traced %s origin: %s", var_name, origin)
            return origin
        
        logger.debug("[DataFlow] Could not trace origin of %s", var_name)
        return None

    # Helper methods
    
    def _extract_call_arguments(self, call_node: ASTNode) -> List[ASTNode]:
        """Extract argument nodes from a method call."""
        arguments = []
        if hasattr(call_node, 'children'):
            # Arguments are typically children of the call node
            for child in call_node.children:
                if child.type in ("argument", "literal", "variable", "methodInvocation"):
                    arguments.append(child)
        return arguments

    def _extract_method_parameters(self, method_def: ASTNode) -> List[Dict]:
        """Extract parameter information from a method definition."""
        parameters = []
        if hasattr(method_def, 'children'):
            for child in method_def.children:
                if child.type == "parameter":
                    param_info = {
                        "name": child.properties.get("name"),
                        "type": child.properties.get("type"),
                        "node": child,
                    }
                    parameters.append(param_info)
        return parameters

    def _extract_argument_value(self, arg_node: ASTNode) -> Optional[str]:
        """Extract the value from an argument node."""
        if arg_node.type == "literal":
            return arg_node.properties.get("value")
        elif arg_node.type == "variable":
            return arg_node.properties.get("name")
        elif arg_node.type == "methodInvocation":
            return arg_node.properties.get("member")
        else:
            return None