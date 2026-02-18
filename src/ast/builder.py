"""
ast/builder.py

Canonical AST construction layer.

Responsibility:
- Construct ASTNode objects
- Assign deterministic IDs
- Wire parent-child relationships
- Produce ASTTree with node index

Non-goals:
- No semantic enrichment
- No symbol resolution
- No graph logic
- No hashing
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from .models import ASTNode, ASTTree

logger = logging.getLogger(__name__)


class ASTBuilder:
    """
    Builder for Canonical ASTTree.

    Guarantees:
    - Deterministic node ID generation (per build run)
    - No global mutable state
    - No silent node dropping
    - Structural integrity preserved
    """

    def __init__(self) -> None:
        self._counter: int = 0
        self._nodes_index: Dict[str, ASTNode] = {}
        logger.debug("ASTBuilder initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_node(
        self,
        node_type: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[ASTNode] = None,
    ) -> ASTNode:
        """
        Create a canonical ASTNode and attach to parent if provided.
        """

        if attributes is None:
            attributes = {}

        node_id = self._generate_id(node_type)

        node = ASTNode(
            id=node_id,
            type=node_type,
            attributes=attributes,
            children=[],
            parent_id=parent.id if parent else None,
        )

        self._nodes_index[node_id] = node

        if parent:
            parent.children.append(node)

        logger.debug(
            "Created node id=%s type=%s parent=%s",
            node_id,
            node_type,
            parent.id if parent else None,
        )

        return node

    def build_tree(
        self,
        root: ASTNode,
        *,
        language: str,
        file_path: str,
    ) -> ASTTree:
        logger.info(
            "Finalizing ASTTree root_id=%s language=%s file=%s",
            root.id,
            language,
            file_path,
        )

        tree = ASTTree(
            root=root,
            language=language,
            file_path=file_path,
        )

        logger.info("ASTTree built successfully")

        return tree


    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _generate_id(self, node_type: str) -> str:
        """
        Deterministic ID generation for current build run.
        Format: <type>_<sequence>
        """

        self._counter += 1
        normalized_type = node_type.lower()
        return f"{normalized_type}_{self._counter}"
