from typing import Any, Dict, Optional, List
from collections import defaultdict

from src.ast.models import ASTNode, ASTLocation


class JavaASTAdapter:
    """
    Converts Java parser AST into canonical ASTNode structure.
    Produces canonical node types: suite | test | node
    """

    def __init__(self):
        self._counters = defaultdict(int)

    # -------------------------------------------------
    # ID Generation (Deterministic + Unique)
    # -------------------------------------------------

    def _generate_id(self, node_type: str) -> str:
        """
        Unique ID per node type.
        Example:
            suite_1
            test_3
            node_12
        """
        self._counters[node_type] += 1
        return f"{node_type}_{self._counters[node_type]}"

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def adapt(self, parsed_root: Any) -> ASTNode:
        self._counters = defaultdict(int)  # Reset counters for deterministic IDs
        return self._convert(parsed_root, parent=None)

    # -------------------------------------------------
    # Core Recursive Conversion
    # -------------------------------------------------

    def _convert(self, parsed_node: Any, parent: Optional[ASTNode]) -> ASTNode:

        canonical_type = self._map_type(parsed_node)
        node_id = self._generate_id(canonical_type)

        ast_node = ASTNode(
            id=node_id,
            type=canonical_type,
            name=getattr(parsed_node, "name", None),
            properties=self._extract_properties(parsed_node),
            location=self._extract_location(parsed_node),
        )

        if parent:
            parent.add_child(ast_node)

        for child in self._extract_children(parsed_node):
            self._convert(child, ast_node)

        return ast_node

    # -------------------------------------------------
    # Canonical Type Mapping
    # -------------------------------------------------

    def _map_type(self, parsed_node: Any) -> str:
        """
        Maps Java parser node types into canonical types.
        """

        node_class = type(parsed_node).__name__

        # Class → suite
        if node_class in ("ClassDeclaration", "InterfaceDeclaration"):
            return "suite"

        # Method with @Test annotation → test
        if node_class == "MethodDeclaration":
            if self._is_test_method(parsed_node):
                return "test"
            return "node"

        return "node"

    def _is_test_method(self, parsed_node: Any) -> bool:
        annotations = getattr(parsed_node, "annotations", [])
        for ann in annotations:
            ann_name = getattr(ann, "name", "")
            if ann_name.lower() == "test":
                return True
        return False

    # -------------------------------------------------
    # Property Extraction (Scalar Only)
    # -------------------------------------------------

    def _extract_properties(self, parsed_node: Any) -> Dict[str, Any]:
        props = {}

        for attr in dir(parsed_node):
            if attr.startswith("_"):
                continue

            value = getattr(parsed_node, attr)

            if isinstance(value, (str, int, float, bool)):
                props[attr] = value

        return props

    # -------------------------------------------------
    # Child Extraction
    # -------------------------------------------------

    def _extract_children(self, parsed_node: Any) -> List[Any]:
        children = []

        for attr in dir(parsed_node):
            if attr.startswith("_"):
                continue

            value = getattr(parsed_node, attr)

            if isinstance(value, list):
                for item in value:
                    if self._is_ast_like(item):
                        children.append(item)

            elif self._is_ast_like(value):
                children.append(value)

        return children

    def _is_ast_like(self, obj: Any) -> bool:
        return hasattr(obj, "__dict__")

    # -------------------------------------------------
    # Location Extraction
    # -------------------------------------------------

    def _extract_location(self, parsed_node: Any) -> Optional[ASTLocation]:
        line = getattr(parsed_node, "line", None)

        if line:
            return ASTLocation(
                start_line=line,
                end_line=line
            )

        return None
