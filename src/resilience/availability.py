"""Availability model.

Each link fails with probability  p * (length_km / 100)  - i.e. p is the
failure probability per 100 km of fibre (the 2017 study swept p from 0 to 0.2).

  path availability        A(path)   = product over links of (1 - p * len/100)
  protected demand (1+1)   A(demand) = 1 - (1 - A(working)) * (1 - A(backup))

The protected formula assumes working and backup fail independently, which is
exactly what disjoint (and SRG-disjoint) routing tries to make true.
"""
from __future__ import annotations

import networkx as nx

from .models import RoutedDemand

FAILURE_PROBABILITIES = [0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2]


def path_availability(g: nx.Graph, path: list[str], p: float) -> float:
    a = 1.0
    for x, y in zip(path, path[1:]):
        a *= max(0.0, 1.0 - p * g[x][y]["length_km"] / 100.0)
    return a


def demand_availability(g: nx.Graph, d: RoutedDemand, p: float) -> float:
    aw = path_availability(g, d.working, p)
    if not d.backup:
        return aw
    ab = path_availability(g, d.backup, p)
    return 1.0 - (1.0 - aw) * (1.0 - ab)


def average_availability(g: nx.Graph, routed: list[RoutedDemand], p: float) -> float:
    return sum(demand_availability(g, d, p) for d in routed) / len(routed)
