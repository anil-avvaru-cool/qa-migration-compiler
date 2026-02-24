"""
Basic call graph builder.

Produces method -> set(called_method_names) mapping. Conservative resolution.
"""
from __future__ import annotations

from typing import Dict, Set, List
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

        self._build()

    def _build(self) -> None:
        # Collect possible method nodes (any node with type 'node' and a name)
        method_nodes: Dict[str, ASTNode] = {}
        for t in self.trees:
            for n in t.walk():
                if n.type in ("node", "test") and n.name:
                    method_nodes[n.name] = n

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
