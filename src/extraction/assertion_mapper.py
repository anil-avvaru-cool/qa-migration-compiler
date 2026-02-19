# src/extraction/assertion_mapper.py

import logging
from typing import List, Dict
from src.ast.models import ASTTree, ASTNode


logger = logging.getLogger(__name__)

class AssertionMapper:
    """
    Extract assertion invocations (MVP).
    """

    def map(self, ast_tree: ASTTree) -> List[Dict]:
        logger.info("Assertion mapping started")

        assertions: List[Dict] = []

        for node in self._walk(ast_tree.root):
            if node.type == "MethodInvocation":
                member = node.properties.get("member")

                if member and member.startswith("assert"):
                    assertions.append({
                        "id": node.id,
                        "assertion": member,
                        "file_path": ast_tree.file_path,
                    })

        logger.info("Assertion mapping completed")
        return assertions

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)
