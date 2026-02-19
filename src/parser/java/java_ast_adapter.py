# src/adapters/java_ast_adapter.py

import logging
from typing import Dict, Any, List

from javalang.tree import Node as JavaNode
from javalang.tree import CompilationUnit

from src.ast.models import ASTNode, ASTTree


logger = logging.getLogger(__name__)


class JavaASTAdapter:
    """
    Converts javalang CompilationUnit into internal ASTTree.

    Responsibilities:
        - Traverse javalang AST
        - Create ASTNode instances
        - Wire parent-child relationships
        - Generate deterministic IDs
        - Preserve full structure (no node dropping)

    Non-Goals:
        - Graph building
        - Symbol resolution
        - Semantic analysis
        - Optimization
    """

    def __init__(self) -> None:
        self._id_counter: int = 0
        self._nodes_index: Dict[str, ASTNode] = {}

    # -----------------------------
    # Public API
    # -----------------------------

    def adapt(
        self,
        compilation_unit: CompilationUnit,
        file_path: str,
    ) -> ASTTree:
        """
        Convert CompilationUnit into ASTTree.

        Args:
            compilation_unit: Root javalang node
            file_path: Source file path

        Returns:
            ASTTree
        """

        logger.info("AST adaptation started: %s", file_path)

        self._reset_state()

        root_node = self._convert_node(compilation_unit, parent=None)

        logger.info("AST adaptation completed: %s", file_path)

        return ASTTree(
            root=root_node,
            language="java",
            file_path=file_path,
        )

    # -----------------------------
    # Internal Helpers
    # -----------------------------

    def _reset_state(self) -> None:
        self._id_counter = 0
        self._nodes_index.clear()

    def _next_id(self) -> str:
        node_id = f"n{self._id_counter}"
        self._id_counter += 1
        return node_id

    def _convert_node(
        self,
        java_node: Any,
        parent: ASTNode | None,
    ) -> ASTNode:
        """
        Recursively convert javalang node to ASTNode.
        """

        if not isinstance(java_node, JavaNode):
            raise TypeError(
                f"Expected JavaNode, got {type(java_node)}"
            )

        node_id = self._next_id()

        ast_node = ASTNode(
            id=node_id,
            type=type(java_node).__name__,
            name = getattr(java_node, "name", None),
            properties=self._extract_properties(java_node),
            children=[],
        )

        # Parent wiring (object-based, not id-based)
        if parent is not None:
            ast_node._parent = parent
            parent.children.append(ast_node)

        self._nodes_index[node_id] = ast_node

        # Recursively process children
        for attr in java_node.attrs:
            value = getattr(java_node, attr)

            if isinstance(value, JavaNode):
                self._convert_node(value, ast_node)

            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, JavaNode):
                        self._convert_node(item, ast_node)

        return ast_node

    def _extract_properties(self, java_node: JavaNode) -> Dict[str, Any]:
        """
        Extract non-node primitive attributes for serialization.
        """

        props: Dict[str, Any] = {}

        for attr in java_node.attrs:
            value = getattr(java_node, attr)

            if isinstance(value, JavaNode):
                continue

            if isinstance(value, list):
                # Skip nested node lists
                if any(isinstance(v, JavaNode) for v in value):
                    continue

            props[attr] = value

        return props
