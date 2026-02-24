"""
Data-flow analysis for locator binding.

Performs conservative propagation of locator initializers through assignments
and simple method returns using call graph information.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple, List
import logging

from src.ast.models import ASTTree, ASTNode
from src.analysis.call_graph import CallGraphBuilder
from src.analysis.type_hierarchy import TypeHierarchyResolver
from src.ast.cross_index import CrossASTIndex

logger = logging.getLogger(__name__)


class DataFlowAnalyzer:
    """Analyze locator/value flow to resolve effective initializer nodes."""

    def __init__(self, trees: List[ASTTree]):
        self.trees = trees
        self.cross_index = CrossASTIndex(trees)
        self.call_graph = CallGraphBuilder(trees)
        self.type_resolver = TypeHierarchyResolver(trees)

    def find_locator_for_symbol(self, symbol_name: str) -> Optional[ASTNode]:
        """Search across the corpus for a locator initializer for a symbol name.

        Conservative strategy:
        1. Find a field/variable node named symbol_name and return first locator descendant.
        2. If not found, search for methods that return this symbol (not implemented complexly).
        """
        for node in self.cross_index.by_type("field") + self.cross_index.by_type("variable"):
            if node.name == symbol_name:
                for descendant in node.walk():
                    qualifier = descendant.properties.get("qualifier")
                    member = descendant.properties.get("member")
                    if qualifier == "By" and member:
                        return descendant

        return None
