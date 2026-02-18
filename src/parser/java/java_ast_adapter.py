"""
parser/java/java_ast_adapter.py

Adapts javalang AST into canonical ASTTree.

Responsibility:
- Traverse javalang AST
- Convert every node into canonical ASTNode
- Preserve structural integrity
- No semantic logic
"""

from __future__ import annotations

import logging
from typing import Any

import javalang

from src.ast.builder import ASTBuilder
from src.ast.models import ASTTree

logger = logging.getLogger(__name__)


class JavaASTAdapter:
    """
    Converts javalang AST into canonical ASTTree.
    """

    def __init__(self) -> None:
        self._builder = ASTBuilder()
        logger.debug("JavaASTAdapter initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def adapt(self, compilation_unit: javalang.tree.CompilationUnit) -> ASTTree:
        """
        Entry point for adapting javalang AST into canonical ASTTree.
        """

        logger.info("Starting Java AST adaptation")

        if compilation_unit is None:
            raise ValueError("Compilation unit cannot be None")

        root_node = self._convert_node(compilation_unit, parent=None)

        tree = self._builder.build_tree(
            root_node,
            language="java",
            file_path=file_path,
        )


        logger.info(
            "Java AST adaptation completed successfully total_nodes=%d",
            len(tree.nodes),
        )

        return tree

    # ------------------------------------------------------------------
    # Internal Conversion
    # ------------------------------------------------------------------

    def _convert_node(self, node: Any, parent) -> Any:
        """
        Recursively convert javalang node into canonical ASTNode.
        """

        # Primitive types are treated as leaf attributes
        if self._is_primitive(node):
            return node

        if isinstance(node, list):
            last_created = None
            for item in node:
                last_created = self._convert_node(item, parent)
            return last_created

        if not isinstance(node, javalang.ast.Node):
            # Unknown object type — preserve as attribute
            return node

        node_type = type(node).__name__
        attributes = self._extract_attributes(node)

        canonical_node = self._builder.create_node(
            node_type=node_type,
            attributes=attributes,
            parent=parent,
        )

        # Recursively process children
        for attr_name in node.attrs:
            value = getattr(node, attr_name)

            if isinstance(value, list):
                for child in value:
                    self._convert_node(child, canonical_node)
            else:
                self._convert_node(value, canonical_node)

        logger.debug(
            "Adapted node type=%s id=%s",
            node_type,
            canonical_node.id,
        )

        return canonical_node

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_attributes(self, node: javalang.ast.Node) -> dict:
        """
        Extract primitive attributes from javalang node.
        Child nodes are excluded (handled separately).
        """

        attributes = {}

        for attr in node.attrs:
            value = getattr(node, attr)

            if self._is_primitive(value):
                attributes[attr] = value

        return attributes

    @staticmethod
    def _is_primitive(value: Any) -> bool:
        """
        Determine if value is JSON-serializable primitive.
        """

        return isinstance(value, (str, int, float, bool)) or value is None
