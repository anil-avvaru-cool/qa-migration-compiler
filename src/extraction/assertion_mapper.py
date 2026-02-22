# src/extraction/assertion_mapper.py

import logging
from typing import List, Dict
from src.ast.models import ASTTree, ASTNode


logger = logging.getLogger(__name__)

class AssertionMapper:
    """
    Extract assertion invocations (MVP).
    """

    def map(self, ast_node: ASTNode) -> List[Dict]:
        logger.info("Assertion mapping started")

        assertions: List[Dict] = []
        seen_ids = set()
        seen_types = set()

        for node in self._walk(ast_node):
            # Skip if we've already processed this exact node
            if node.id in seen_ids:
                continue

            member = node.properties.get("member")

            if member and member.startswith("assert"):
                # Deduplicate: count each assertion type only once
                if member not in seen_types:
                    seen_ids.add(node.id)
                    seen_types.add(member)
                    assertions.append({
                        "type": "assertion",
                        "name": member,
                        "target": None,
                        "parameters": {},
                    })

        logger.info("Assertion mapping completed")
        return assertions

    def _walk(self, node: ASTNode):
        yield node
        for child in node.children:
            yield from self._walk(child)
