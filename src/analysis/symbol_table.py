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
        
        # Maps method name -> (method_node, inferred_target_name)
        # Example: "enterEmail" -> (node, "emailInput")
        # Used to resolve page object method calls to their targets
        self.method_targets: Dict[str, Tuple[ASTNode, str]] = {}
        
        # Maps class/type name -> field initializers
        # Example: "LoginPage" -> {"emailInput": locator_node, ...}
        self.class_fields: Dict[str, Dict[str, ASTNode]] = {}

    def build_from_tree(self, ast_tree: ASTTree) -> None:
        """
        Scan AST tree and populate symbol table with:
        1. Variable/field initializations (locators)
        2. Page object class structure (fields and methods)
        3. Method -> target mappings (inferred from method names and usage)
        """
        logger.info("Building symbol table from AST tree")

        # First pass: record all symbols and class structure
        for node in ast_tree.walk():
            # Look for field declarations with initializers
            if node.type in ("field", "variable"):
                self._record_field_initializer(node)
            # Also check method argument declarations
            elif node.type == "parameter":
                self._record_field_initializer(node)
            # Record page object classes
            elif node.type == "suite":
                self._record_class_structure(node)
        
        # Second pass: infer method targets from field names and method signatures
        self._infer_method_targets(ast_tree)

        logger.info(
            "Symbol table built: %d symbols, %d methods, %d classes",
            len(self.symbols),
            len(self.method_targets),
            len(self.class_fields),
        )

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
        Enhanced resolution of a step's target from a statement node.
        Returns (target_name_id, target_node_id) if found, else None.

        Resolution strategy (in order of priority):
        1. Page object method calls (e.g., loginPage.enterEmail() -> emails field)
        2. Direct symbol references (variables/fields)
        3. Direct By.* locator nodes
        """
        # Walk the statement and look for references or locators
        for node in self._walk(stmt_node):
            # Priority 1: Check if this is a page object method call
            method_target = self._resolve_method_target(node)
            if method_target:
                return method_target
            
            # Priority 2: Check if this is a direct reference to a symbol
            resolved = self.resolve_reference(node)
            if resolved:
                var_name, init_node = resolved
                return (var_name, init_node.id)

            # Priority 3: Check if this is itself a locator node
            if self._is_locator_node(node):
                strategy = node.properties.get("member", "locator")
                return (strategy, node.id)

        return None

    def _record_class_structure(self, class_node: ASTNode) -> None:
        """
        Record all fields and methods of a page object class.
        This enables us to understand what targets a class provides.
        """
        class_name = class_node.name
        if not class_name:
            return
        
        class_fields = {}
        
        # Find all field initializers in this class
        for child in class_node.children:
            if child.type == "field":
                field_name = child.name
                if field_name:
                    # Look for By.* locator initializer
                    for descendant in self._walk(child):
                        if self._is_locator_node(descendant):
                            class_fields[field_name] = descendant
                            logger.debug(f"Class {class_name} field: {field_name}")
                            break
        
        if class_fields:
            self.class_fields[class_name] = class_fields
    
    def _infer_method_targets(self, ast_tree: ASTTree) -> None:
        """
        Infer method -> target mappings by analyzing method names.
        Page object methods follow patterns like:
          - enterEmail -> accesses emailInput field
          - clickLogin -> accesses loginButton field
          - selectCountry -> accesses countrySelect field
        """
        for node in ast_tree.walk():
            if node.type == "node" and node.name:
                method_name = node.name
                # Check for common method name patterns
                inferred_target = self._infer_target_from_method_name(method_name)
                if inferred_target:
                    self.method_targets[method_name] = (node, inferred_target)
                    logger.debug(f"Inferred method target: {method_name} -> {inferred_target}")
    
    def _infer_target_from_method_name(self, method_name: str) -> Optional[str]:
        """
        Infer target name from method name using common page object patterns.
        Examples:
          - enterEmail -> emailInput
          - clickLogin -> loginButton
          - selectCountry -> countrySelect
          - checkTerms -> termsCheckbox
        """
        # Common method name patterns
        if method_name.startswith("enter"):
            # enterEmail -> email, enterPassword -> password
            field = method_name[5:].lower()  # Remove "enter"
            return f"{field}Input"
        elif method_name.startswith("click"):
            # clickLogin -> loginButton
            field = method_name[5:].lower()
            return f"{field}Button"
        elif method_name.startswith("select"):
            # selectCountry -> countrySelect
            field = method_name[6:].lower()
            return f"{field}Select"
        elif method_name.startswith("check"):
            # checkTerms -> termsCheckbox
            field = method_name[5:].lower()
            return f"{field}Checkbox"
        elif method_name.startswith("fill"):
            # fillForm -> formInput
            field = method_name[4:].lower()
            return f"{field}Input"
        
        return None
    
    def _resolve_method_target(self, node: ASTNode) -> Optional[Tuple[str, str]]:
        """
        Resolve page object method calls to their targets.
        Example: loginPage.enterEmail() -> ("emailInput", node.id)
        
        Checks if node is a method call we have inferred the target for.
        """
        member = node.properties.get("member")
        if not member or member not in self.method_targets:
            return None
        
        # Found a method we know about - return the inferred target
        method_node, inferred_target = self.method_targets[member]
        return (inferred_target, node.id)

    def _walk(self, node: ASTNode):
        """Depth-first traversal of node subtree."""
        yield node
        for child in node.children:
            yield from self._walk(child)
