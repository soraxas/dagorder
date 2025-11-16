import pytest

from dagorder import Node, TaskScheduler


def test_basic_schedule():
    nodes = {
        "A": Node(id="A", payload=None, deps=[], priority=1),
        "B": Node(id="B", payload=None, deps=["A"], priority=2),
        "C": Node(id="C", payload=None, deps=["A"], priority=0),
    }
    scheduler = TaskScheduler(nodes)
    order = scheduler.compute_order(enabled_leaves={"B", "C"})
    assert order[0] == "A"
    assert order[-1] in {"B", "C"}


def test_pruning():
    nodes = {
        "A": Node(id="A", payload=None, deps=[], priority=0),
        "B": Node(id="B", payload=None, deps=["A"], priority=0),
        "C": Node(id="C", payload=None, deps=["A"], priority=0),
    }
    scheduler = TaskScheduler(nodes)
    order = scheduler.compute_order(enabled_leaves={"B"})
    assert "C" not in order
    assert set(order) == {"A", "B"}


@pytest.fixture
def large_graph() -> dict[str, Node]:
    return {
        "A": Node("A", None, deps=[], priority=5),
        "B": Node("B", None, deps=["A"], priority=2),
        "C": Node("C", None, deps=["A"], priority=3),
        "D": Node("D", None, deps=["A"], priority=1),
        "E": Node("E", None, deps=["B"]),
        "F": Node("F", None, deps=["B"], priority=4),
        "G": Node("G", None, deps=["C"]),
        "H": Node("H", None, deps=["D"]),
        "I": Node("I", None, deps=["D"]),
        "J": Node("J", None, deps=["E", "F"]),
        "K": Node("K", None, deps=["H", "I"]),
        "L": Node("L", None, deps=["J", "K"]),
        "M": Node("M", None, deps=["J"], priority=10),
    }


def test_needed_nodes(large_graph: dict[str, Node]):
    nodes = large_graph
    scheduler = TaskScheduler(nodes)
    needed = scheduler.compute_needed_nodes({"J"})
    assert needed == {"F", "J", "E", "B", "A"}


def test_large_graph(large_graph: dict[str, Node]):
    r"""
    Graph shape:

           A
        /  |   \
       B   C    D
      / \  |   / \
     E   F G  H   I
       \ /   \   /
        J      K
        | \   /
        M   L   <- leaf enabled
    """
    nodes = large_graph
    scheduler = TaskScheduler(nodes)
    order = scheduler.compute_order(enabled_leaves={"L", "M", "C"})

    # All nodes needed for L or F must be present
    assert "A" in order
    assert "B" in order
    assert "F" in order
    assert "L" in order

    # Nodes unrelated to L or F should be pruned
    assert "G" not in order
    assert "D" in order  # D is needed because K is needed
    assert "I" in order
    assert "H" in order

    # Must respect dependency: parents must appear before children
    positions = {id: order.index(id) for id in order}

    def before(x, y):
        assert positions[x] < positions[y]

    before("A", "B")
    before("A", "D")
    before("B", "F")
    before("F", "J")
    before("J", "L")
    before("D", "H")
    before("D", "I")
    before("H", "K")
    before("I", "K")
    before("K", "L")
    before("A", "C")

    # F has high priority; it should come early once ready
    assert positions["F"] < positions["E"]
    # M has high priority; it should come early once ready
    assert positions["M"] < positions["L"]

    # M has the highest priority; it should come first
    assert positions["M"] == len(scheduler.compute_order(enabled_leaves={"M"}))
