"""
Type hierarchy resolver.

Builds parent -> children relationships and provides small utilities
for merging inherited members.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set
import logging

from src.ast.models import ASTNode, ASTTree

logger = logging.getLogger(__name__)


class TypeHierarchyResolver:
    """Resolve class inheritance within a corpus of AST trees.

    Strategy:
    - Scan for nodes of type 'suite' (classes/interfaces)
    - Determine declared parent(s) via:
      * `properties['extends']` if present (string or list)
      * child nodes representing types with `name` set
    - Build maps: parent -> {children}, class -> {parents}
    """

    def __init__(self, trees: List[ASTTree]):
        self.trees = trees
        self.class_nodes: Dict[str, ASTNode] = {}
        self.parents: Dict[str, List[str]] = {}
        self.children: Dict[str, List[str]] = {}

        self._build()

    def _build(self) -> None:
        # Collect suite nodes by name
        for t in self.trees:
            for n in t.walk():
                if n.type == "suite" and n.name:
                    self.class_nodes[n.name] = n

        # Resolve parent links
        for name, node in list(self.class_nodes.items()):
            declared_parents = self._extract_declared_parents(node)
            if declared_parents:
                self.parents[name] = declared_parents
                for p in declared_parents:
                    self.children.setdefault(p, []).append(name)

        logger.debug("[TypeHierarchy] Resolved %d classes", len(self.class_nodes))

    def _extract_declared_parents(self, node: ASTNode) -> List[str]:
        # Check properties first (adapter may expose 'extends' as scalar)
        props = node.properties or {}
        parents: List[str] = []

        extends = props.get("extends")
        if extends:
            if isinstance(extends, list):
                parents.extend([str(p) for p in extends if p])
            else:
                parents.append(str(extends))

        # Also check children that might represent types
        for child in node.children:
            if child.type == "node" and child.name:
                # A child with name may represent a type reference
                if child.name not in parents:
                    parents.append(child.name)

        return parents

    def get_parents(self, class_name: str) -> List[str]:
        return list(self.parents.get(class_name, []))

    def get_children(self, class_name: str) -> List[str]:
        return list(self.children.get(class_name, []))

    def linearized_mro(self, class_name: str) -> List[str]:
        """Return a simple linearization of inheritance (DFS order).

        This is intentionally simplistic and suited to resolution use-cases
        where Java multiple-inheritance via interfaces is not deeply relied upon.
        """
        seen: Set[str] = set()
        order: List[str] = []

        def visit(cn: str):
            if cn in seen:
                return
            seen.add(cn)
            for p in self.get_parents(cn):
                visit(p)
            order.append(cn)

        visit(class_name)
        return order
