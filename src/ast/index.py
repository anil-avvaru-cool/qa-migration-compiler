"""
AST Index

Responsibility:
- Provide O(1) node lookup by id
- Provide parent lookup
- Provide filtered traversal utilities

Non-Goals:
- No semantic resolution
- No graph construction
- No mutation of AST
- No incremental logic
"""

from __future__ import annotations

from typing import Dict, List, Optional, Iterable
import logging

from .models import ASTTree, ASTNode

logger = logging.getLogger(__name__)


class ASTIndex:
    """
    Read-only index over an ASTTree.

    Designed for:
    - Fast lookup
    - Parent navigation
    - Efficient analysis layer consumption
    """

    def __init__(self, tree: ASTTree):
        self._tree = tree
        self._id_map: Dict[str, ASTNode] = {}
        self._type_index: Dict[str, List[ASTNode]] = {}

        self._build_index()

    # ---------------------------------------------------------
    # Index Construction
    # ---------------------------------------------------------

    def _build_index(self) -> None:
        logger.debug("[ASTIndex] Building index")

        for node in self._tree.walk():

            if node.id in self._id_map:
                raise ValueError(
                    f"Duplicate AST node id detected: {node.id}"
                )

            self._id_map[node.id] = node

            # Type-based index (optional but cheap)
            self._type_index.setdefault(node.type, []).append(node)

        logger.debug(
            f"[ASTIndex] Index built with {len(self._id_map)} nodes"
        )

    # ---------------------------------------------------------
    # Lookup APIs
    # ---------------------------------------------------------

    def get(self, node_id: str) -> Optional[ASTNode]:
        """
        O(1) node lookup by ID.
        """
        return self._id_map.get(node_id)

    def require(self, node_id: str) -> ASTNode:
        """
        Strict lookup. Raises if not found.
        """
        node = self.get(node_id)
        if node is None:
            raise KeyError(f"AST node not found: {node_id}")
        return node

    def parent_of(self, node: ASTNode) -> Optional[ASTNode]:
        """
        Returns parent node using parent_id.
        """
        if not node.parent_id:
            return None
        return self._id_map.get(node.parent_id)

    def children_of(self, node: ASTNode) -> List[ASTNode]:
        """
        Returns direct children.
        """
        return node.children

    # ---------------------------------------------------------
    # Filtering Utilities
    # ---------------------------------------------------------

    def by_type(self, node_type: str) -> List[ASTNode]:
        """
        Returns all nodes of a given type.
        """
        return list(self._type_index.get(node_type, []))

    def all_nodes(self) -> Iterable[ASTNode]:
        return self._id_map.values()

    def size(self) -> int:
        return len(self._id_map)
