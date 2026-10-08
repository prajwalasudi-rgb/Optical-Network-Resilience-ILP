# Original 2017 code

The code as submitted in 2017, unchanged. Written for **Python 2.7** and
**Gurobi 7** (commercial solver), so it does not run on a current setup
without changes. Use the maintained version in [`../src/`](../src/) instead.

| File | Content |
|---|---|
| `input_data.py` | read GraphML topologies, demands and SRGs; link lengths; Basemap network plot |
| `optimize_ilp.py` | Gurobi ILP models: unprotected, link disjoint, node disjoint, SRG disjoint, combined; availability sweep |
| `results.py` | runs all models on the four European topologies and plots average path lengths |
| `figures_2017/` | network plots produced at the time |

Original dependencies: `gurobipy` (Gurobi 7.0.2), `networkx` 1.x, `geopy` (`vincenty`,
removed in geopy 2.0), `matplotlib` with `mpl_toolkits.basemap`, `numpy`.

Running it required the data files (now in `../data/eu/`) in the same folder:

```
python2 results.py
```
