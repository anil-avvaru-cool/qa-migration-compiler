from src.utils.hashing import deterministic_hash
from src.utils.graph_utils import DirectedGraph


def test_deterministic_hash_stable():
    value = "test::login"
    assert deterministic_hash(value) == deterministic_hash(value)


def test_graph_basic():
    graph = DirectedGraph()
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")

    assert not graph.has_cycle()
    assert graph.topological_sort() == ["A", "B", "C"]
