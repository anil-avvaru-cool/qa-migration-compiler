"""
ast/hasher.py

Structural hashing for Canonical AST layer.

Responsibility:
- Deterministic structural hash generation for ASTNode and ASTTree.
- No semantic resolution.
- No graph construction.
- No mutation of AST.

MVP:
- Bottom-up structural hashing.
- Stable attribute ordering.
- JSON-serializable intermediate representation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Dict, Any

from .models import ASTNode, ASTTree

logger = logging.getLogger(__name__)


class ASTHasher:
    """
    Deterministic structural hasher for AST.

    Guarantees:
    - Order-stable hashing.
    - No global state.
    - No AST mutation.
    - Safe for incremental comparison usage.
    """

    def __init__(self, algorithm: str = "sha256") -> None:
        self._algorithm = algorithm
        logger.debug("ASTHasher initialized with algorithm=%s", algorithm)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def hash_tree(self, tree: ASTTree) -> str:
        """
        Compute deterministic structural hash of entire ASTTree.
        """
        logger.info("Starting AST tree hashing")
        root_hash = self.hash_node(tree.root)
        logger.info("Completed AST tree hashing root_id=%s hash=%s",
                    tree.root.id, root_hash)
        return root_hash

    def hash_node(self, node: ASTNode) -> str:
        """
        Compute deterministic structural hash of a node (bottom-up).
        """

        logger.debug("Hashing node id=%s type=%s", node.id, node.type)

        # Hash children first (preserve order)
        child_hashes = [
            self.hash_node(child)
            for child in node.children
        ]

        structural_payload = self._build_structural_payload(
            node=node,
            child_hashes=child_hashes
        )

        node_hash = self._compute_hash(structural_payload)

        logger.debug(
            "Node hashed id=%s hash=%s",
            node.id,
            node_hash
        )

        return node_hash

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _build_structural_payload(
        self,
        node: ASTNode,
        child_hashes: list[str]
    ) -> Dict[str, Any]:
        """
        Build deterministic, JSON-serializable structure for hashing.

        IMPORTANT:
        - Excludes runtime-only fields.
        - Excludes parent references.
        - Attributes sorted.
        """

        # Ensure deterministic attribute ordering
        sorted_attributes = dict(sorted(node.attributes.items()))

        payload = {
            "type": node.type,
            "attributes": sorted_attributes,
            "children": child_hashes,
        }

        return payload

    def _compute_hash(self, payload: Dict[str, Any]) -> str:
        """
        Compute cryptographic hash of structural payload.
        """

        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        hasher = hashlib.new(self._algorithm)
        hasher.update(serialized.encode("utf-8"))

        return hasher.hexdigest()
