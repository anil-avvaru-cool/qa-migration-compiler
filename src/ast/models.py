"""
Canonical AST Models

Layer Responsibility:
- Define language-agnostic AST structure
- Preserve structural integrity
- Provide safe JSON-serializable models
- Enforce deterministic ID discipline
- Maintain parent-child consistency

Non-Goals:
- No semantic logic
- No graph building
- No symbol resolution
- No optimization
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# AST Location
# ---------------------------------------------------------

class ASTLocation(BaseModel):
    """
    Represents source code position.
    """

    file_path: Optional[str] = None
    start_line: Optional[int] = None
    start_column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    class Config:
        frozen = True


# ---------------------------------------------------------
# AST Node
# ---------------------------------------------------------

class ASTNode(BaseModel):
    """
    Canonical AST Node.

    Structural only.
    Language-agnostic.
    """

    id: str
    type: str
    name: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)  # Arbitrary key-value pairs
    
    parent_id: Optional[str] = None
    children: List["ASTNode"] = Field(default_factory=list)

    location: Optional[ASTLocation] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = False
        validate_assignment = True

    # -------------------------
    # Structural Safeguards
    # -------------------------

    @model_validator(mode="after")
    def validate_structure(self):
        """
        Ensures no silent structural corruption.
        """

        # ID must exist
        if not self.id:
            raise ValueError("ASTNode.id cannot be empty")

        # type must exist
        if not self.type:
            raise ValueError("ASTNode.type cannot be empty")

        # Children must not reference self
        for child in self.children:
            if child.id == self.id:
                raise ValueError(f"Node {self.id} cannot be its own child")

            if child.parent_id and child.parent_id != self.id:
                raise ValueError(
                    f"Child {child.id} parent_id mismatch (expected {self.id})"
                )

        return self

    # -------------------------
    # Safe Child Attachment
    # -------------------------

    def add_child(self, child: "ASTNode") -> None:
        """
        Safely attach a child node.
        Ensures parent_id consistency.
        """
        if child.id == self.id:
            raise ValueError("Cannot attach node to itself")

        child.parent_id = self.id
        self.children.append(child)

        logger.debug(
            f"[AST] Attached child {child.id} to parent {self.id}"
        )

    # -------------------------
    # Traversal
    # -------------------------

    def walk(self) -> List["ASTNode"]:
        """
        Depth-first traversal.
        """
        nodes = [self]
        for child in self.children:
            nodes.extend(child.walk())
        return nodes


# Required for forward reference resolution
ASTNode.model_rebuild()


# ---------------------------------------------------------
# AST Tree
# ---------------------------------------------------------

class ASTTree(BaseModel):
    """
    Represents a full file AST.
    """

    root: ASTNode
    language: str
    file_path: str

    class Config:
        validate_assignment = True

    @model_validator(mode="after")
    def validate_root(self):
        if not self.root:
            raise ValueError("ASTTree must have a root node")

        if not self.file_path:
            raise ValueError("ASTTree.file_path cannot be empty")

        return self

    # -------------------------
    # Utility APIs
    # -------------------------

    def walk(self) -> List[ASTNode]:
        return self.root.walk()

    def to_dict(self) -> Dict[str, Any]:
        """
        Deterministic JSON-safe serialization.
        """
        return self.model_dump()

    def node_count(self) -> int:
        return len(self.walk())
