"""Loading topologies, traffic demands and shared-risk groups."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
from geopy.distance import geodesic

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def read_network(path: str | Path) -> nx.Graph:
    """Read a GraphML topology and annotate every link with its length in km."""
    g = nx.read_graphml(path)
    for u, v in g.edges():
        a = (g.nodes[u]["Latitude"], g.nodes[u]["Longitude"])
        b = (g.nodes[v]["Latitude"], g.nodes[v]["Longitude"])
        g[u][v]["length_km"] = round(geodesic(a, b).km, 2)
    return g


def read_demands(path: str | Path) -> list[tuple[str, str, int]]:
    """Demand file lines: '<source> <destination> <capacity>'."""
    demands = []
    for line in Path(path).read_text().splitlines():
        if line.strip():
            src, dst, cap = line.split()
            demands.append((src, dst, int(cap)))
    return demands


@dataclass
class SharedRiskGroup:
    """Elements that can fail together (e.g. fibres in the same duct).

    links: undirected links (u, v) in the group
    nodes: nodes in the group (e.g. sites in the same building/region)
    """
    name: str
    links: list[tuple[str, str]] = field(default_factory=list)
    nodes: list[str] = field(default_factory=list)


def read_srgs(path: str | Path) -> list[SharedRiskGroup]:
    """Two formats are supported:

    link groups:  SRG1 (Munich, Berlin) (Hamburg, Frankfurt)
    node groups:  SRG1 Bremen Hannover Hamburg
    """
    groups = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        name, rest = line.split(None, 1)
        pairs = re.findall(r"\(\s*([^,()]+?)\s*,\s*([^,()]+?)\s*\)", rest)
        if pairs:
            groups.append(SharedRiskGroup(name, links=[(a, b) for a, b in pairs]))
        else:
            groups.append(SharedRiskGroup(name, nodes=rest.split()))
    return groups


def dataset_paths(region: str, topology: str, demand: str) -> tuple[Path, Path, Path | None]:
    """Paths of a topology, demand set and (if present) SRG file in data/<region>/."""
    folder = DATA_DIR / region
    srg = next(iter(sorted(folder.glob("srg_*.txt"))), None)
    return folder / f"{topology}.graphml", folder / f"{demand}.txt", srg
