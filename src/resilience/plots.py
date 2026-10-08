"""Figures: network map with routed paths, availability curves, path-length bars."""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402

from .availability import FAILURE_PROBABILITIES, average_availability  # noqa: E402
from .models import RoutedDemand  # noqa: E402

# Validated categorical palette (fixed order) and chart chrome
SCHEME_STYLE = {
    "unprotected":   ("#2a78d6", "o", "Unprotected"),
    "link_disjoint": ("#eb6834", "s", "Link disjoint"),
    "node_disjoint": ("#1baf7a", "^", "Node disjoint"),
    "srg_disjoint":  ("#eda100", "D", "SRG disjoint"),
    "combined":      ("#e87ba4", "v", "Node + SRG disjoint"),
}
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
WORKING, BACKUP = "#2a78d6", "#eb6834"


def _style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _pos(g):
    """Equirectangular projection, x scaled by cos(mean latitude)."""
    lat0 = sum(g.nodes[n]["Latitude"] for n in g) / len(g)
    k = math.cos(math.radians(lat0))
    return {n: (g.nodes[n]["Longitude"] * k, g.nodes[n]["Latitude"]) for n in g}


def plot_network_paths(g: nx.Graph, routed: list[RoutedDemand], title: str, out: Path) -> Path:
    pos = _pos(g)
    fig, ax = plt.subplots(figsize=(8, 8), dpi=110)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    nx.draw_networkx_edges(g, pos, ax=ax, edge_color=AXIS, width=1)
    for d in routed:
        if d.backup:
            nx.draw_networkx_edges(g, pos, ax=ax, edgelist=list(zip(d.backup, d.backup[1:])),
                                   edge_color=BACKUP, width=2.5, style=(0, (4, 2)))
        nx.draw_networkx_edges(g, pos, ax=ax, edgelist=list(zip(d.working, d.working[1:])),
                               edge_color=WORKING, width=2.5)
    endpoints = {n for d in routed for n in (d.source, d.target)}
    nx.draw_networkx_nodes(g, pos, ax=ax, node_size=28, node_color=SURFACE,
                           edgecolors=MUTED, linewidths=1)
    nx.draw_networkx_nodes(g, pos, ax=ax, nodelist=sorted(endpoints), node_size=60,
                           node_color=INK, edgecolors=SURFACE, linewidths=1.5)
    for n, (x, y) in pos.items():
        ax.text(x, y + 0.35, n, fontsize=7, ha="center", va="bottom",
                color=INK if n in endpoints else INK2)
    ax.plot([], [], color=WORKING, lw=2.5, label="Working path")
    if any(d.backup for d in routed):
        ax.plot([], [], color=BACKUP, lw=2.5, ls=(0, (4, 2)), label="Backup path")
    ax.legend(loc="lower left", frameon=False, fontsize=9)
    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


def plot_availability(g: nx.Graph, routed_by_scheme: dict[str, list[RoutedDemand]],
                      title: str, out: Path) -> Path:
    xs = [p * 100 for p in FAILURE_PROBABILITIES]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=110)
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    for scheme, routed in routed_by_scheme.items():
        color, marker, label = SCHEME_STYLE[scheme]
        ys = [average_availability(g, routed, p) * 100 for p in FAILURE_PROBABILITIES]
        ax.plot(xs, ys, color=color, lw=2, marker=marker, ms=6,
                markeredgecolor=SURFACE, markeredgewidth=1.2, label=label)
    ax.set_xlim(0, xs[-1])
    ax.set_ylim(0, 102)
    ax.set_xlabel("link failure probability per 100 km (%)", fontsize=9, color=MUTED)
    ax.set_ylabel("average demand availability (%)", fontsize=9, color=MUTED)
    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


def plot_path_lengths(rows: list[dict], title: str, out: Path) -> Path:
    topologies = list(dict.fromkeys(r["topology"] for r in rows))
    schemes = [s for s in SCHEME_STYLE if any(r["scheme"] == s for r in rows)]
    width = 0.8 / len(schemes)
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=110)
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    for k, scheme in enumerate(schemes):
        color, _m, label = SCHEME_STYLE[scheme]
        vals = [next(r["avg_total_km"] for r in rows if r["topology"] == t and r["scheme"] == scheme)
                for t in topologies]
        xs = [i + (k - (len(schemes) - 1) / 2) * width for i in range(len(topologies))]
        ax.bar(xs, vals, width=width * 0.92, color=color, label=label, edgecolor=SURFACE, linewidth=1)
    ax.set_xticks(range(len(topologies)))
    ax.set_xticklabels([t.replace("network_", "") for t in topologies], fontsize=9, color=INK2)
    ax.set_ylabel("avg. working + backup length per demand (km)", fontsize=9, color=MUTED)
    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.legend(frameon=False, fontsize=8, ncol=5, loc="upper left", bbox_to_anchor=(0, -0.08))
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out
