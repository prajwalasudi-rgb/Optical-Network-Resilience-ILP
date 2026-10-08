"""Integer linear programs for (protected) path routing.

For every demand r = (s, t) and every directed arc (i, j) of the network:

    u[r,i,j] = 1  if the WORKING path of r uses arc (i, j)
    v[r,i,j] = 1  if the BACKUP  path of r uses arc (i, j)   (protected schemes)

Objective   minimise the total length of all working + backup paths
Constraints
  flow conservation   one unit of flow from s to t, for u and for v
  LINK disjoint       u[r,i,j] + u[r,j,i] + v[r,i,j] + v[r,j,i] <= 1
  NODE disjoint       working and backup share no transit node
  SRG disjoint        if the working path touches a shared-risk group,
                      the backup path must not touch it (and vice versa)
  COMBINED            node disjoint + SRG disjoint

The formulations follow the 2017 Gurobi models in ``original/``; they are
written with PuLP here so they solve with the free HiGHS solver (or Gurobi /
CBC if installed).
"""
from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import pulp

from .data import SharedRiskGroup

SCHEMES = ["unprotected", "link_disjoint", "node_disjoint", "srg_disjoint", "combined"]


@dataclass
class RoutedDemand:
    source: str
    target: str
    capacity: int
    working: list[str]
    backup: list[str] | None

    def path_length(self, g: nx.Graph, path: list[str] | None) -> float:
        if not path:
            return 0.0
        return sum(g[a][b]["length_km"] for a, b in zip(path, path[1:]))


def _arcs_to_path(arcs: list[tuple[str, str]], source: str, target: str) -> list[str]:
    nxt = dict(arcs)
    path, node = [source], source
    while node != target:
        node = nxt[node]
        path.append(node)
    return path


def _default_solver(msg: bool = False):
    for name in ("HiGHS", "GUROBI", "PULP_CBC_CMD"):
        if name in pulp.listSolvers(onlyAvailable=True):
            return pulp.getSolver(name, msg=msg)
    raise RuntimeError("No MILP solver available - install highspy (pip install highspy)")


def solve(g: nx.Graph, demands: list[tuple[str, str, int]], scheme: str,
          srgs: list[SharedRiskGroup] | None = None, solver=None) -> list[RoutedDemand]:
    """Route all demands with the given protection scheme; returns optimal paths."""
    if scheme not in SCHEMES:
        raise ValueError(f"unknown scheme '{scheme}', choose from {SCHEMES}")
    protected = scheme != "unprotected"
    node_disjoint = scheme in ("node_disjoint", "combined")
    srg_disjoint = scheme in ("srg_disjoint", "combined")
    srgs = srgs or []

    arcs = [(i, j) for i, j in g.edges()] + [(j, i) for i, j in g.edges()]
    length = {(i, j): g[i][j]["length_km"] for i, j in arcs}
    R = range(len(demands))
    node_idx = {n: k for k, n in enumerate(g.nodes())}

    prob = pulp.LpProblem(f"routing_{scheme}", pulp.LpMinimize)

    def binaries(prefix):
        return {(r, i, j): pulp.LpVariable(f"{prefix}_{r}_{k}", cat="Binary")
                for r in R for k, (i, j) in enumerate(arcs)}

    u = binaries("u")
    v = binaries("v") if protected else {}

    prob += pulp.lpSum(length[i, j] * (u[r, i, j] + (v[r, i, j] if protected else 0))
                       for r in R for i, j in arcs)

    for r, (s, t, _cap) in enumerate(demands):
        if s not in g or t not in g:
            raise ValueError(f"demand {s}->{t}: node not in topology")
        for n in g.nodes():
            rhs = 1 if n == t else (-1 if n == s else 0)
            into = [(i, j) for i, j in arcs if j == n]
            out = [(i, j) for i, j in arcs if i == n]
            prob += (pulp.lpSum(u[r, i, j] for i, j in into)
                     - pulp.lpSum(u[r, i, j] for i, j in out) == rhs), f"flow_u_{r}_{node_idx[n]}"
            if protected:
                prob += (pulp.lpSum(v[r, i, j] for i, j in into)
                         - pulp.lpSum(v[r, i, j] for i, j in out) == rhs), f"flow_v_{r}_{node_idx[n]}"

        if not protected:
            continue

        # link disjoint (both directions of a link count as the same link)
        for i, j in g.edges():
            prob += (u[r, i, j] + u[r, j, i] + v[r, i, j] + v[r, j, i] <= 1), f"link_{r}_{node_idx[i]}_{node_idx[j]}"

        # node disjoint: each transit node carries at most one of the two paths
        if node_disjoint:
            for n in g.nodes():
                if n in (s, t):
                    continue
                prob += (pulp.lpSum(u[r, i, j] + v[r, i, j] for i, j in arcs if i == n) <= 1,
                         f"node_{r}_{node_idx[n]}")

        # SRG disjoint: working and backup never both touch the same risk group
        if srg_disjoint:
            for k, grp in enumerate(srgs):
                uw = pulp.LpVariable(f"srg_w_{r}_{k}", cat="Binary")
                ub = pulp.LpVariable(f"srg_b_{r}_{k}", cat="Binary")
                for a, b in grp.links:
                    if not g.has_edge(a, b):
                        continue
                    prob += uw >= u[r, a, b] + u[r, b, a]
                    prob += ub >= v[r, a, b] + v[r, b, a]
                for n in grp.nodes:
                    if n not in g or n in (s, t):
                        continue
                    for i, j in arcs:
                        if n in (i, j):
                            prob += uw >= u[r, i, j]
                            prob += ub >= v[r, i, j]
                prob += uw + ub <= 1, f"srg_{r}_{k}"

    status = prob.solve(solver or _default_solver())
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"{scheme}: solver status {pulp.LpStatus[status]} "
                           "(no feasible routing - topology may not allow this protection)")

    routed = []
    for r, (s, t, cap) in enumerate(demands):
        w_arcs = [(i, j) for i, j in arcs if u[r, i, j].value() > 0.5]
        b_arcs = [(i, j) for i, j in arcs if protected and v[r, i, j].value() > 0.5]
        routed.append(RoutedDemand(
            s, t, cap,
            working=_arcs_to_path(w_arcs, s, t),
            backup=_arcs_to_path(b_arcs, s, t) if protected else None,
        ))
    return routed
