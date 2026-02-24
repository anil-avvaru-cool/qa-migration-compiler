"""
Basic call graph builder.

Produces method -> set(called_method_names) mapping. Conservative resolution.
"""
from __future__ import annotations

from typing import Dict, Set, List, Tuple, Optional
import logging

from src.ast.models import ASTTree, ASTNode
from src.ast.cross_index import CrossASTIndex
from src.analysis.type_hierarchy import TypeHierarchyResolver

logger = logging.getLogger(__name__)


class CallGraphBuilder:
    """Build a conservative call graph across a corpus of AST trees."""

    def __init__(self, trees: List[ASTTree]):
        self.trees = trees
        self.cross_index = CrossASTIndex(trees)
        self.type_resolver = TypeHierarchyResolver(trees)

        # method name -> set of called method names
        self.graph: Dict[str, Set[str]] = {}
        
        # NEW: Index of method definitions: (class_name, method_name) -> ASTNode
        self.method_defs: Dict[Tuple[str, str], ASTNode] = {}
        
        # NEW: Index of class definitions: class_name -> ASTNode
        self.class_defs: Dict[str, ASTNode] = {}

        self._build()

    def _build(self) -> None:
        # Collect possible method nodes (any node with type 'node' and a name)
        method_nodes: Dict[str, ASTNode] = {}
        for t in self.trees:
            for n in t.walk():
                if n.type in ("node", "test") and n.name:
                    method_nodes[n.name] = n
                
                # NEW: Track method definitions by (class_name, method_name)
                if n.type in ("node", "test", "method") and n.name:
                    class_name = self._get_enclosing_class(n)
                    if class_name:
                        self.method_defs[(class_name, n.name)] = n
                        logger.debug("[CallGraph] Registered method: %s.%s", class_name, n.name)
                
                # NEW: Track class definitions
                if n.type in ("class", "classDeclaration") and n.name:
                    self.class_defs[n.name] = n
                    logger.debug("[CallGraph] Registered class: %s", n.name)

        # Walk all nodes and find call sites (properties.member)
        # _id_map stores lists of nodes (one per file), iterate each node
        for node_id, nodes in list(self.cross_index._id_map.items()):
            for node in nodes:
                member = node.properties.get("member")
                if member and isinstance(member, str):
                    # We conservatively map this call to any known method with this name
                    callers = self._find_enclosing_methods(node)
                    for caller in callers:
                        self.graph.setdefault(caller, set()).add(member)

        logger.debug("[CallGraph] Built graph with %d caller entries", len(self.graph))
        logger.debug("[CallGraph] Indexed %d method definitions", len(self.method_defs))
        logger.debug("[CallGraph] Indexed %d class definitions", len(self.class_defs))

    def _find_enclosing_methods(self, node: ASTNode) -> List[str]:
        # Walk parents until we find a method-like node
        cur = node
        while cur and cur.parent_id:
            parent = self.cross_index.get(cur.parent_id)
            if parent is None:
                break
            if parent.type in ("node", "test") and parent.name:
                return [parent.name]
            cur = parent
        return ["<unknown>"]

    def callers(self, method_name: str) -> List[str]:
        return [m for m, callees in self.graph.items() if method_name in callees]

    def callees(self, method_name: str) -> List[str]:
        return list(self.graph.get(method_name, []))

    # NEW METHODS FOR WEEK 1
    
    def resolve_method_definition(self, class_name: str, method_name: str) -> Optional[ASTNode]:
        """
        Resolve a method definition to its ASTNode.
        
        Args:
            class_name: Name of the class containing the method
            method_name: Name of the method to resolve
            
        Returns:
            ASTNode for the method definition, or None if not found
            
        Example:
            method_def = call_graph.resolve_method_definition("ProductPage", "navigateToProducts")
            # Returns ASTNode for ProductPage.navigateToProducts() method
        """
        method_key = (class_name, method_name)
        if method_key in self.method_defs:
            return self.method_defs[method_key]
        
        # Try without class name (fallback for ambiguous cases)
        for (cls, meth), node in self.method_defs.items():
            if meth == method_name:
                logger.debug("[CallGraph] Resolved %s.%s -> %s", class_name, method_name, node.name)
                return node
        
        logger.debug("[CallGraph] Could not resolve method definition: %s.%s", class_name, method_name)
        return None

    def resolve_method_body(self, class_name: str, method_name: str) -> List[ASTNode]:
        """
        Return all statements in the body of a method.
        
        Args:
            class_name: Name of the class containing the method
            method_name: Name of the method
            
        Returns:
            List of ASTNode statements in method body, empty list if method not found
            
        Example:
            body = call_graph.resolve_method_body("ProductPage", "navigateToProducts")
            # Returns [driver.get(...), waitFor(...), ...]
        """
        method_def = self.resolve_method_definition(class_name, method_name)
        if method_def:
            # Method body is typically the children of the method node
            body = [child for child in method_def.children]
            logger.debug("[CallGraph] Resolved method body for %s.%s: %d statements", 
                        class_name, method_name, len(body))
            return body
        
        logger.debug("[CallGraph] No method body found for %s.%s", class_name, method_name)
        return []

    def find_internal_calls(
        self,
        class_name: str,
        method_name: str,
        target_method: str,
        target_qualifier: str = "driver"
    ) -> List[ASTNode]:
        """
        Find specific method calls inside another method.
        
        Args:
            class_name: Name of the class containing the method
            method_name: Name of the method to search within
            target_method: Name of the method to find calls to (e.g., "get")
            target_qualifier: Qualifier of the target method (e.g., "driver")
            
        Returns:
            List of ASTNode objects representing calls to the target method
            
        Example:
            calls = call_graph.find_internal_calls("ProductPage", "navigateToProducts", "get", "driver")
            # Returns [driver.get(...)] nodes inside navigateToProducts()
        """
        body = self.resolve_method_body(class_name, method_name)
        if not body:
            logger.debug("[CallGraph] No method body for %s.%s, cannot find internal calls", 
                        class_name, method_name)
            return []
        
        found_calls = []
        for stmt in self._walk_body(body):
            member = stmt.properties.get("member")
            qualifier = stmt.properties.get("qualifier")
            
            if member == target_method and qualifier == target_qualifier:
                logger.debug("[CallGraph] Found internal call: %s.%s() in %s.%s()", 
                            qualifier, member, class_name, method_name)
                found_calls.append(stmt)
        
        return found_calls

    def _walk_body(self, nodes: List[ASTNode]) -> List[ASTNode]:
        """Walk through list of nodes and yield all descendants."""
        for node in nodes:
            yield node
            for child in node.walk():
                yield child

    def _get_enclosing_class(self, node: ASTNode) -> Optional[str]:
        """Get the class name that encloses a node."""
        cur = node
        while cur:
            if cur.type in ("class", "classDeclaration") and cur.name:
                return cur.name
            if hasattr(cur, 'parent_id') and cur.parent_id:
                cur = self.cross_index.get(cur.parent_id)
            else:
                break
        return None
