# DAG Order

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/soraxas/dagorder/main.svg)](https://results.pre-commit.ci/latest/github/soraxas/dagorder/main)

A Python library for computing priority-aware topological ordering of nodes in a directed acyclic graph (DAG).

## Features

- **Priority-based ordering**: Higher priority nodes are scheduled first when dependencies allow
- **Dependency tracking**: Respects node dependencies to ensure correct execution order
- **Pruning**: Only computes order for nodes needed to reach enabled leaf nodes
- **Visualization**: Export graphs to DOT format for visualization with Graphviz

## Installation

```bash
uv add dagorder
```

## Quick Start

```python
from dagorder import Node, TaskScheduler

# Define nodes with dependencies and priorities
nodes = {
    "A": Node("A", None, deps=[], priority=5),
    "B": Node("B", None, deps=["A"], priority=2),
    "C": Node("C", None, deps=["A"], priority=3),
}

scheduler = TaskScheduler(nodes)

# Compute execution order for enabled leaf nodes
order = scheduler.compute_order(enabled_leaves={"B", "C"})
# Result: ["A", "C", "B"] - C comes before B due to higher priority
```

## Result

```sh
uv run --with numpy examples/run.py
```
Example graph:

<img width="919" height="702" alt="dag" src="https://github.com/user-attachments/assets/0a12bcac-c6b8-4abe-931a-c01c231c7f0b" />

With only needing the results from nodes `M`, `L`, `C` (with some custom task priority), `dagorder` provided the compute order of
```
A -> B -> E -> F -> J -> [M] (priority 10)
[C] (priority 3)
D -> H -> I -> K -> L (priority 0)
```



