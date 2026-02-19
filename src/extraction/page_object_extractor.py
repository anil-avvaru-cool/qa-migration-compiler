# src/extraction/page_object_extractor.py

import logging
from typing import List, Dict
from src.ast.models import ASTTree, ASTNode


logger = logging.getLogger(__name__)


class PageObjectExtractor:
    """
    Extract Java classes as Page Objects (MVP).
    """

    def extract(self, ast_tree: ASTTree) -> List[Dict]:
        logger.info("PageObject extraction started")

        pages: List[Dict] = []

        for node in self._walk(ast_tree.root):
            if node.type == "ClassDeclaration":
                logger.debug(f"Found class: {node}")
                pages.append({
                    "id": node.id,
                    "name": node.name,
                    "file_path": ast_tree.file_path,
                })

        logger.info("PageObject extraction completed")
        return pages

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)
