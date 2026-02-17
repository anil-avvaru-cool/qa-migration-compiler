"""
Java Parser → Canonical AST

Responsibility:
- Convert Java source into canonical ASTTree
- Preserve structure only
- No semantic analysis
- No IR emission
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import javalang

from src.parser.base_parser import BaseParser
from src.ast.models import ASTNode, ASTTree, ASTLocation


class JavaParser(BaseParser):

    language = "java"

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def parse(self, file_path: str) -> ASTTree:
        self.logger.info(f"[JavaParser] Parsing file: {file_path}")

        path = Path(file_path)
        source = path.read_text(encoding="utf-8")

        try:
            compilation_unit = javalang.parse.parse(source)
        except Exception as e:
            self.logger.error(f"[JavaParser] Parse error: {e}")
            raise

        root_id = self._generate_id("compilation_unit", file_path)

        root = ASTNode(
            id=root_id,
            type="CompilationUnit",
            name=path.name,
            location=ASTLocation(file_path=file_path),
        )

        # Package
        if compilation_unit.package:
            root.add_child(
                self._build_package(compilation_unit.package, file_path)
            )

        # Imports
        for imp in compilation_unit.imports:
            root.add_child(
                self._build_import(imp, file_path)
            )

        # Types (classes/interfaces/enums)
        for type_decl in compilation_unit.types:
            root.add_child(
                self._build_type(type_decl, file_path)
            )

        tree = ASTTree(
            root=root,
            language=self.language,
            file_path=file_path,
        )

        self.logger.info(
            f"[JavaParser] Completed parsing {file_path} "
            f"({tree.node_count()} nodes)"
        )

        return tree

    # ---------------------------------------------------------
    # Builders
    # ---------------------------------------------------------

    def _build_package(self, package, file_path: str) -> ASTNode:
        node = ASTNode(
            id=self._generate_id("package", package.name),
            type="PackageDeclaration",
            name=package.name,
            location=self._safe_location(package, file_path),
        )
        return node

    def _build_import(self, imp, file_path: str) -> ASTNode:
        node = ASTNode(
            id=self._generate_id("import", imp.path),
            type="ImportDeclaration",
            name=imp.path,
            location=self._safe_location(imp, file_path),
            metadata={
                "static": imp.static,
                "wildcard": imp.wildcard,
            },
        )
        return node

    def _build_type(self, type_decl, file_path: str) -> ASTNode:
        node = ASTNode(
            id=self._generate_id("type", type_decl.name),
            type=type_decl.__class__.__name__,
            name=type_decl.name,
            location=self._safe_location(type_decl, file_path),
            metadata={
                "modifiers": list(type_decl.modifiers or []),
            },
        )

        # Fields
        for field in getattr(type_decl, "fields", []):
            for declarator in field.declarators:
                node.add_child(
                    self._build_field(field, declarator, file_path)
                )

        # Methods
        for method in getattr(type_decl, "methods", []):
            node.add_child(
                self._build_method(method, file_path)
            )

        # Constructors
        for ctor in getattr(type_decl, "constructors", []):
            node.add_child(
                self._build_constructor(ctor, file_path)
            )

        # Nested types
        for inner in getattr(type_decl, "types", []):
            node.add_child(
                self._build_type(inner, file_path)
            )

        return node

    def _build_field(self, field, declarator, file_path: str) -> ASTNode:
        return ASTNode(
            id=self._generate_id("field", declarator.name),
            type="FieldDeclaration",
            name=declarator.name,
            location=self._safe_location(field, file_path),
            metadata={
                "type": getattr(field.type, "name", None),
                "modifiers": list(field.modifiers or []),
            },
        )

    def _build_method(self, method, file_path: str) -> ASTNode:
        node = ASTNode(
            id=self._generate_id("method", method.name),
            type="MethodDeclaration",
            name=method.name,
            location=self._safe_location(method, file_path),
            metadata={
                "return_type": getattr(method.return_type, "name", None),
                "modifiers": list(method.modifiers or []),
            },
        )

        # Parameters (structural only)
        for param in method.parameters:
            node.add_child(
                ASTNode(
                    id=self._generate_id(
                        "parameter", f"{method.name}:{param.name}"
                    ),
                    type="Parameter",
                    name=param.name,
                    location=self._safe_location(param, file_path),
                    metadata={
                        "type": getattr(param.type, "name", None),
                    },
                )
            )

        return node

    def _build_constructor(self, ctor, file_path: str) -> ASTNode:
        node = ASTNode(
            id=self._generate_id("constructor", ctor.name),
            type="ConstructorDeclaration",
            name=ctor.name,
            location=self._safe_location(ctor, file_path),
            metadata={
                "modifiers": list(ctor.modifiers or []),
            },
        )

        for param in ctor.parameters:
            node.add_child(
                ASTNode(
                    id=self._generate_id(
                        "parameter", f"{ctor.name}:{param.name}"
                    ),
                    type="Parameter",
                    name=param.name,
                    location=self._safe_location(param, file_path),
                    metadata={
                        "type": getattr(param.type, "name", None),
                    },
                )
            )

        return node

    # ---------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------

    def _safe_location(self, node, file_path: str) -> Optional[ASTLocation]:
        if hasattr(node, "position") and node.position:
            return ASTLocation(
                file_path=file_path,
                start_line=node.position.line,
                start_column=node.position.column,
            )
        return ASTLocation(file_path=file_path)
