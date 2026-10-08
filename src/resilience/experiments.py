"""Run every protection scheme on every topology of a region and collect results."""
from __future__ import annotations

import csv
from pathlib import Path

from .availability import FAILURE_PROBABILITIES, average_availability
from .data import DATA_DIR, read_demands, read_network, read_srgs
from .models import SCHEMES, solve
from .plots import plot_availability, plot_network_paths, plot_path_lengths


def run_region(region: str, demand: str, out_dir: Path, schemes=SCHEMES) -> list[dict]:
    folder = DATA_DIR / region
    out_dir.mkdir(parents=True, exist_ok=True)
    srg_file = next(iter(sorted(folder.glob("srg_*.txt"))), None)
    srgs = read_srgs(srg_file) if srg_file else []
    demands = read_demands(folder / f"{demand}.txt")

    rows = []
    for topo_file in sorted(folder.glob("*.graphml")):
        topology = topo_file.stem
        g = read_network(topo_file)
        routed_by_scheme = {}
        for scheme in schemes:
            try:
                routed = solve(g, demands, scheme, srgs)
            except RuntimeError as exc:
                print(f"  {topology:28s} {scheme:14s} infeasible ({exc})")
                continue
            routed_by_scheme[scheme] = routed
            work = sum(d.path_length(g, d.working) for d in routed) / len(routed)
            back = sum(d.path_length(g, d.backup) for d in routed) / len(routed)
            row = {"region": region, "topology": topology, "demand": demand, "scheme": scheme,
                   "nodes": g.number_of_nodes(), "links": g.number_of_edges(),
                   "avg_working_km": round(work, 1), "avg_backup_km": round(back, 1),
                   "avg_total_km": round(work + back, 1)}
            for p in FAILURE_PROBABILITIES:
                row[f"A@p={p}"] = round(average_availability(g, routed, p), 5)
            rows.append(row)
            print(f"  {topology:28s} {scheme:14s} working {work:7.1f} km  backup {back:7.1f} km"
                  f"  A(p=0.05) = {row['A@p=0.05']:.4f}")

            if scheme == "combined" and len(routed) > 1:
                ex = routed[1]
                plot_network_paths(g, [ex], f"{ex.source} \u2192 {ex.target} · {topology} · "
                                   "node + SRG disjoint protection",
                                   out_dir / f"map_example_{topology}.png")
            if scheme in ("unprotected", "combined"):
                plot_network_paths(g, routed, f"{topology} · {demand} · {scheme.replace('_', ' ')}",
                                   out_dir / f"map_{topology}_{scheme}.png")
        if routed_by_scheme:
            plot_availability(g, routed_by_scheme, f"Availability · {topology} · {demand}",
                              out_dir / f"availability_{topology}.png")

    if rows:
        plot_path_lengths(rows, f"Path length by protection scheme · {region.upper()} · {demand}",
                          out_dir / "path_lengths.png")
        with open(out_dir / "summary.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    return rows
