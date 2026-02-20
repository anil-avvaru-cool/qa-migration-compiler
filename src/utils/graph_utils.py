from collections import defaultdict, deque
from typing import Dict, Set, List


class DirectedGraph:
    """
    Minimal directed graph utility.
    Layer-agnostic.
    """

    def __init__(self):
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node: str) -> None:
        self._adjacency.setdefault(node, set())

    def add_edge(self, source: str, target: str) -> None:
        self._adjacency[source].add(target)
        self._adjacency.setdefault(target, set())

    def neighbors(self, node: str) -> Set[str]:
        return self._adjacency.get(node, set())

    def nodes(self) -> List[str]:
        return list(self._adjacency.keys())

    def edges(self) -> List[tuple]:
        return [
            (src, tgt)
            for src, targets in self._adjacency.items()
            for tgt in targets
        ]

    def has_cycle(self) -> bool:
        """
        Detect cycle using Kahn's algorithm.
        """
        in_degree = {node: 0 for node in self._adjacency}

        for targets in self._adjacency.values():
            for target in targets:
                in_degree[target] += 1

        queue = deque([n for n, d in in_degree.items() if d == 0])
        visited = 0

        while queue:
            node = queue.popleft()
            visited += 1
            for neighbor in self._adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return visited != len(self._adjacency)

    def topological_sort(self) -> List[str]:
        """
        Return topological ordering.
        Raises ValueError if cycle exists.
        """
        in_degree = {node: 0 for node in self._adjacency}

        for targets in self._adjacency.values():
            for target in targets:
                in_degree[target] += 1

        queue = deque([n for n, d in in_degree.items() if d == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in self._adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self._adjacency):
            raise ValueError("Graph contains a cycle")

        return order
