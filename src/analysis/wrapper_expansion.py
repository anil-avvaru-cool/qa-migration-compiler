"""
Wrapper method expansion utilities.

Detects simple wrappers (single-call delegators) and expands chains multi-level.
"""
from __future__ import annotations

from typing import List, Dict
import logging

from src.ast.models import ASTTree, ASTNode
from src.ast.cross_index import CrossASTIndex

logger = logging.getLogger(__name__)


class WrapperExpander:
    """Detect and expand wrapper/delegating methods."""

    def __init__(self, trees: List[ASTTree]):
        self.trees = trees
        self.cross_index = CrossASTIndex(trees)

    def find_wrapper_chain(self, start_method_name: str, depth_limit: int = 10) -> List[str]:
        """Follow delegating wrappers to produce a call chain of method names.

        Heuristic: a wrapper method is a method node that contains a single child
        which is a call node (properties.member) and no other statements.
        """
        chain: List[str] = [start_method_name]
        seen = set(chain)

        cur = start_method_name
        for _ in range(depth_limit):
            next_name = self._find_single_delegate(cur)
            if not next_name or next_name in seen:
                break
            chain.append(next_name)
            seen.add(next_name)
            cur = next_name

        return chain

    def _find_single_delegate(self, method_name: str) -> str:
        # Find method node by name
        for node in self.cross_index.by_type("node") + self.cross_index.by_type("test"):
            if node.name == method_name:
                # Look for a single call child
                call_children = [c for c in node.walk() if c.properties.get("member")]
                if len(call_children) == 1:
                    return call_children[0].properties.get("member")
        return ""
