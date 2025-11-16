from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Node(Generic[T]):
    id: str
    payload: T
    deps: list[str]
    priority: int = 0
    """
    Priority of the node.
    The node always gets its priority from its descendants, if any of them have a priority higher than its own.
    """
    priority_from_descendants: int = 0

    @property
    def overall_priority(self) -> int:
        """
        The priority of the node, considering the priority of its descendants.
        """
        return max(self.priority, self.priority_from_descendants)


@dataclass
class TaskScheduler(Generic[T]):
    nodes: dict[str, Node[T]]
    # descendants: dict[str, list[Node[T]]]

    def __post_init__(self):
        leaf_nodes = set(self.nodes.keys())
        # leaf nodes are the ones that have no one depending on them.
        for node in self.nodes.values():
            for dep in node.deps:
                leaf_nodes.discard(dep)
        if len(leaf_nodes) == 0:
            raise ValueError("No leaf nodes found in the graph. Cyclic dependency?")

        # do a bfs
        queue = list(leaf_nodes)
        visited = set()
        while queue:
            node_key = queue.pop()
            visited.add(node_key)
            # update the parent's priority
            for parent_key in self.nodes[node_key].deps:
                parent = self.nodes[parent_key]
                node = self.nodes[node_key]
                # update the parent's priority from its descendants
                # which results in recursive updates of the parent's priority
                self.nodes[parent_key].priority_from_descendants = max(
                    parent.priority_from_descendants, node.overall_priority
                )

            for dep in self.nodes[node_key].deps:
                if dep not in visited:
                    queue.append(dep)

        if visited != set(self.nodes.keys()):
            raise ValueError(
                "Not all nodes were visited in the graph. Disconnected graph?"
            )

    # ---------------------------------------------
    #   Reverse reachability: which nodes are needed
    # ---------------------------------------------
    def compute_needed_nodes(self, enabled_leaves: set[str]) -> set[str]:
        # Reverse edges map parent → children
        reverse_edges: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for nid, node in self.nodes.items():
            for dep in node.deps:
                reverse_edges[dep].append(nid)

        needed: set[str] = set()
        stack = list(enabled_leaves)

        while stack:
            nid = stack.pop()
            if nid in needed:
                continue
            needed.add(nid)
            for parent in self.nodes[nid].deps:
                stack.append(parent)

        return needed

    # ---------------------------------------------
    #   Compute priority-aware topological order
    # ---------------------------------------------
    def compute_order(self, enabled_leaves: set[str]) -> list[str]:
        needed = self.compute_needed_nodes(enabled_leaves)

        # Compute in-degree only for needed nodes
        in_degree: dict[str, int] = {nid: 0 for nid in needed}

        reverse_edges: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for nid, node in self.nodes.items():
            for dep in node.deps:
                reverse_edges[dep].append(nid)

        for nid in needed:
            for dep in self.nodes[nid].deps:
                if dep in needed:
                    in_degree[nid] += 1

        # Max-heap via (-priority)
        heap: list[tuple[int, str]] = []
        for nid, deg in in_degree.items():
            if deg == 0:
                heapq.heappush(heap, (-self.nodes[nid].overall_priority, nid))

        order: list[str] = []
        while heap:
            _, nid = heapq.heappop(heap)
            order.append(nid)

            for child in reverse_edges[nid]:
                if child in needed:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        heapq.heappush(
                            heap, (-self.nodes[child].overall_priority, child)
                        )

        return order

    # ---------------------------------------------
    #        DOT Graph Export for Visualization
    # ---------------------------------------------
    def as_dot_string(self) -> str:
        """
        Return a DOT graph representation for Graphviz.
        Useful for debugging.
        """
        lines = ["digraph DAG {"]

        for nid, node in self.nodes.items():
            # Add node with priority as label
            lines.append(
                f'    "{nid}" [label="{nid}\\np={node.priority}\\noverall={node.overall_priority}"];'
            )
            for dep in node.deps:
                lines.append(f'    "{dep}" -> "{nid}";')

        lines.append("}")
        return "\n".join(lines)
