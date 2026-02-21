# src/extraction/action_mapper.py

import logging
from typing import List, Dict
from src.ast.models import ASTTree, ASTNode


logger = logging.getLogger(__name__)


SUPPORTED_ACTIONS = {"click", "sendKeys", "submit"}


class ActionMapper:
    """
    Extract Selenium interaction methods (MVP).
    """

    def map(self, ast_node: ASTNode) -> List[Dict]:
        logger.info("Action mapping started")

        actions: List[Dict] = []

        for node in self._walk(ast_node):
            if node.type == "MethodInvocation":
                member = node.properties.get("member")

                if member in SUPPORTED_ACTIONS:
                    actions.append({
                        "id": node.id,
                        "action": member,
                        "file_path": ast_tree.file_path,
                    })

        logger.info("Action mapping completed")
        return actions

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)
