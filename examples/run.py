import pydot
import soraxas_toolbox as st

import dagorder
from dagorder import Node

nodes = {
    "A": Node("A", None, deps=[], priority=5),
    "B": Node("B", None, deps=["A"], priority=2),
    "C": Node("C", None, deps=["A"], priority=3),
    "D": Node("D", None, deps=["A"], priority=1),
    "E": Node("E", None, deps=["B"]),
    "F": Node("F", None, deps=["B"]),
    "G": Node("G", None, deps=["C"]),
    "H": Node("H", None, deps=["D"]),
    "I": Node("I", None, deps=["D"]),
    "J": Node("J", None, deps=["E", "F"]),
    "K": Node("K", None, deps=["H", "I"]),
    "L": Node("L", None, deps=["J", "K"]),
    "M": Node("M", None, deps=["J"], priority=10),
}
scheduler = dagorder.TaskScheduler(nodes)
order = scheduler.compute_order(enabled_leaves={"M", "L", "C"})
# print(order)

graphs = pydot.graph_from_dot_data(scheduler.as_dot_string())
st.image.display(*graphs)

print(order)
print(scheduler.compute_needed_nodes({"M"}))

for node in nodes.values():
    print(node.id, node.overall_priority)
