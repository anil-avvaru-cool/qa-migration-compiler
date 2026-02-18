import pytest
import sys
import os
import logging
from pathlib import Path

from src.ast.builder import ASTBuilder

# Create a logger for this module
logger = logging.getLogger(__name__)

def test_parent_child_wiring():
    logger.info(f" Starting test_parent_child_wiring")
    builder = ASTBuilder()

    # Create root
    root = builder.create_node("CompilationUnit")

    # Create child
    class_node = builder.create_node("ClassDeclaration", parent=root)

    # Create grandchild
    method_node = builder.create_node("MethodDeclaration", parent=class_node)

    tree = builder.build_tree(
        root,
        language="java",
        file_path="/test.java",
    )

    # --- Validate parent relationships ---
    assert class_node.parent_id == root.id
    assert method_node.parent_id == class_node.id

    # --- Validate child wiring ---
    assert len(root.children) == 1
    assert root.children[0].id == class_node.id

    assert len(class_node.children) == 1
    assert class_node.children[0].id == method_node.id

    # --- Validate tree index ---
    assert any(item.id == root.id for item in tree.walk()), f"Root ID {root.id} not found in the list"
    assert any(item.id == class_node.id for item in tree.walk()), f"Class ID {class_node.id} not found in the list"
    assert any(item.id == method_node.id for item in tree.walk()), f"Method ID {method_node.id} not found in the list"
    

def test_deterministic_id_order():
    logger.info(f" Starting test_deterministic_id_order")
    builder = ASTBuilder()

    # Create root
    root = builder.create_node("CompilationUnit")

    # Create child
    class_node = builder.create_node("ClassDeclaration", parent=root)

    # Create grandchild
    method_node = builder.create_node("MethodDeclaration", parent=class_node)

    field_node = builder.create_node("FieldDeclaration", parent=method_node)

    tree = builder.build_tree(
        root,
        language="java",
        file_path="/test1.java",
    )
    ids = []
    logger.debug(f"tree node count: {len(tree.walk())}")
    for node in tree.walk():
        logger.info(f"Node: {node.type}, ID: {node.id}")
        ids.append(node.id)

    # Expected deterministic sequence:
    # compilationunit_1
    # classdeclaration_2
    # methoddeclaration_3
    # fielddeclaration_4

    assert ids[0] == "compilationunit_1"
    assert ids[1] == "classdeclaration_2"
    assert ids[2] == "methoddeclaration_3"
    assert ids[3] == "fielddeclaration_4"

    # Ensure ordering is strictly increasing
    numeric_parts = [int(i.split("_")[-1]) for i in ids]
    assert numeric_parts == sorted(numeric_parts)
