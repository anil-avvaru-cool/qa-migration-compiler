"""
Symbol Table for target resolution.

Builds a symbol table of variable/field initializers (especially locators)
and resolves references to them in method calls.

Responsibility:
- Traverse AST and record variable/field name -> locator node mappings
- Resolve method call arguments to their initializer nodes
- Enable robust target linking across the source hierarchy
"""

import logging
from typing import Dict, Optional, Tuple
from src.ast.models import ASTNode, ASTTree

logger = logging.getLogger(__name__)


class SymbolTable:
    """
    Tracks variable/field initializations (especially locators like By.cssSelector(...))
    and resolves references to them.
    """

    def __init__(self):
        # Maps variable/field name -> AST node of the initializer value
        # Example: "username" -> node of By.cssSelector("#username")
        self.symbols: Dict[str, ASTNode] = {}

    def build_from_tree(self, ast_tree: ASTTree) -> None:
        """
        Scan AST tree and populate symbol table with variable/field initializations.
        Focuses on locator fields (By.* calls).
        """
        logger.info("Building symbol table from AST tree")

        for node in ast_tree.walk():
            # Look for field declarations with initializers
            if node.type in ("field", "variable"):
                self._record_field_initializer(node)
            # Also check method argument declarations
            elif node.type == "parameter":
                self._record_field_initializer(node)

        logger.info("Symbol table built: %d symbols", len(self.symbols))

    def _record_field_initializer(self, var_node: ASTNode) -> None:
        """
        If this variable/field has an initializer that is a locator (By.* call),
        record the mapping name -> initializer node.
        """
        var_name = var_node.name
        if not var_name:
            return

        # Try to find an initializer child (look for a By.* node in subtree)
        for child in var_node.children:
            if self._is_locator_node(child):
                self.symbols[var_name] = child
                logger.debug(f"Recorded symbol: {var_name} -> {child.id}")
                return

            # Recursively check child's children
            for descendant in self._walk(child):
                if self._is_locator_node(descendant):
                    self.symbols[var_name] = descendant
                    logger.debug(f"Recorded symbol: {var_name} -> {descendant.id}")
                    return

    def _is_locator_node(self, node: ASTNode) -> bool:
        """Check if node is a By.* locator call."""
        qualifier = node.properties.get("qualifier")
        member = node.properties.get("member")
        return qualifier == "By" and member is not None

    def resolve_reference(self, node: ASTNode) -> Optional[Tuple[str, ASTNode]]:
        """
        Attempt to resolve a node reference to a variable/field.
        Returns (variable_name, initializer_node) if found, else None.

        This handles cases like:
          driver.findElement(username).sendKeys(user)
        where 'username' is a field reference that we can resolve to its initializer.
        """
        # Check if this node is a reference to a recorded symbol
        name = node.properties.get("name")
        member = node.properties.get("member")

        # Try name first (direct variable reference)
        if name and name in self.symbols:
            return (name, self.symbols[name])

        # Try member (method/field name)
        if member and member in self.symbols:
            return (member, self.symbols[member])

        return None

    def resolve_step_target(self, stmt_node: ASTNode) -> Optional[Tuple[str, str]]:
        """
        Best-effort resolution of a step's target from a statement node.
        Returns (target_name_id, target_node_id) if found, else None.

        Walks the statement tree and finds:
        1. Any references to recorded symbols (variables/fields)
        2. Any By.* locator nodes
        """
        # Walk the statement and look for references or locators
        for node in self._walk(stmt_node):
            # Check if this is a reference to a symbol
            resolved = self.resolve_reference(node)
            if resolved:
                var_name, init_node = resolved
                return (var_name, init_node.id)

            # Check if this is itself a locator node
            if self._is_locator_node(node):
                # Use the locator's strategy (e.g., cssSelector) as name if not found above
                strategy = node.properties.get("member", "locator")
                return (strategy, node.id)

        return None

    def _walk(self, node: ASTNode):
        """Depth-first traversal of node subtree."""
        yield node
        for child in node.children:
            yield from self._walk(child)
