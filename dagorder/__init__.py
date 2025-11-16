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


@dataclass
class TaskScheduler(Generic[T]):
    nodes: dict[str, Node[T]]

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
                heapq.heappush(heap, (-self.nodes[nid].priority, nid))

        order: list[str] = []

        while heap:
            _, nid = heapq.heappop(heap)
            order.append(nid)

            for child in reverse_edges[nid]:
                if child in needed:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        heapq.heappush(heap, (-self.nodes[child].priority, child))

        return order

    # ---------------------------------------------
    #        DOT Graph Export for Visualization
    # ---------------------------------------------
    def visualize(self) -> str:
        """
        Return a DOT graph representation for Graphviz.
        Useful for debugging.
        """
        lines = ["digraph DAG {"]

        for nid, node in self.nodes.items():
            if not node.deps:
                lines.append(f'    "{nid}";')
            for dep in node.deps:
                lines.append(f'    "{dep}" -> "{nid}";')

        lines.append("}")
        return "\n".join(lines)
