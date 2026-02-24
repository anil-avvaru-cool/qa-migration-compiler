"""
Cross-file AST index.

Provides unified lookup across multiple ASTTree objects.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Iterable
import logging

from .models import ASTTree, ASTNode

logger = logging.getLogger(__name__)


class CrossASTIndex:
    """Index over many ASTTree instances.

    - Unified id map (ids must already be unique per tree run)
    - Map file_path -> ASTTree
    - Type-based queries across the corpus
    """

    def __init__(self, trees: Iterable[ASTTree]):
        self._trees_by_file: Dict[str, ASTTree] = {}
        # Allow multiple nodes to share the same id across independent files
        # (adapters generate per-file deterministic ids). Store lists to
        # preserve all occurrences and return the first match by default.
        self._id_map: Dict[str, List[ASTNode]] = {}
        self._type_index: Dict[str, List[ASTNode]] = {}

        for t in trees:
            self._add_tree(t)

    def _add_tree(self, tree: ASTTree) -> None:
        if tree.file_path in self._trees_by_file:
            raise ValueError(f"Duplicate ASTTree file path: {tree.file_path}")

        self._trees_by_file[tree.file_path] = tree

        for node in tree.walk():
            # Append to list for this id (allow duplicates across files)
            self._id_map.setdefault(node.id, []).append(node)
            self._type_index.setdefault(node.type, []).append(node)

        logger.debug("[CrossASTIndex] Added tree %s (%d nodes)", tree.file_path, len(tree.walk()))

    def get(self, node_id: str) -> Optional[ASTNode]:
        """Return the first node with the given id if present (conservative)."""
        lst = self._id_map.get(node_id)
        if not lst:
            return None
        return lst[0]

    def require(self, node_id: str) -> ASTNode:
        n = self.get(node_id)
        if n is None:
            raise KeyError(f"AST node not found: {node_id}")
        return n

    def by_type(self, node_type: str) -> List[ASTNode]:
        return list(self._type_index.get(node_type, []))

    def trees(self) -> Iterable[ASTTree]:
        return self._trees_by_file.values()

    def files(self) -> List[str]:
        return list(self._trees_by_file.keys())
