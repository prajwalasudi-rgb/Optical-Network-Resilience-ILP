"""python -m resilience [--region eu|ger|us] [--demand NAME] [--out results/]"""
from __future__ import annotations

import argparse
from pathlib import Path

from .experiments import run_region


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="resilience",
                                description="Resilient routing in optical core networks (ILP)")
    p.add_argument("--region", default="eu", choices=["eu", "ger", "us"])
    p.add_argument("--demand", default=None,
                   help="demand set, e.g. demand_eu_small (default: <region> small)")
    p.add_argument("--out", type=Path, default=Path("results"))
    a = p.parse_args(argv)
    demand = a.demand or f"demand_{a.region}_small"
    print(f"Region {a.region.upper()}, demands '{demand}'")
    run_region(a.region, demand, a.out / f"{a.region}_{demand}")
    print(f"Results written to {a.out / f'{a.region}_{demand}'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
