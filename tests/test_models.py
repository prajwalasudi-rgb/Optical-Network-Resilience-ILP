import networkx as nx
import pytest

from resilience.availability import demand_availability, path_availability
from resilience.data import SharedRiskGroup, dataset_paths, read_demands, read_network, read_srgs
from resilience.models import RoutedDemand, solve


def grid():
    """Small test network (lengths in km):

        A --100-- B --100-- C
        |         |         |
       100       100       100
        |         |         |
        D --100-- E --100-- F
        |                   |
        +--------500--------+   (D-F long link)
    """
    g = nx.Graph()
    for a, b, km in [("A", "B", 100), ("B", "C", 100), ("A", "D", 100), ("B", "E", 100),
                     ("C", "F", 100), ("D", "E", 100), ("E", "F", 100), ("D", "F", 500)]:
        g.add_edge(a, b, length_km=km)
    return g


def links(path):
    return {frozenset(e) for e in zip(path, path[1:])}


def test_unprotected_is_shortest_path():
    g = grid()
    [d] = solve(g, [("A", "F", 1)], "unprotected")
    assert d.backup is None
    assert d.path_length(g, d.working) == nx.shortest_path_length(g, "A", "F", weight="length_km")


def test_link_disjoint_paths_share_no_link():
    g = grid()
    [d] = solve(g, [("A", "F", 1)], "link_disjoint")
    assert d.working[0] == d.backup[0] == "A" and d.working[-1] == d.backup[-1] == "F"
    assert not links(d.working) & links(d.backup)


def test_node_disjoint_paths_share_no_transit_node():
    g = grid()
    [d] = solve(g, [("A", "F", 1)], "node_disjoint")
    assert not set(d.working[1:-1]) & set(d.backup[1:-1])


def test_srg_disjoint_respects_shared_risk_group():
    g = grid()
    # A-B and D-E run in the same duct: working and backup must not use both
    srg = [SharedRiskGroup("duct", links=[("A", "B"), ("D", "E")])]
    [d] = solve(g, [("A", "F", 1)], "srg_disjoint", srg)
    in_w = links(d.working) & {frozenset(("A", "B")), frozenset(("D", "E"))}
    in_b = links(d.backup) & {frozenset(("A", "B")), frozenset(("D", "E"))}
    assert not (in_w and in_b)
    # the cheapest link-disjoint pair (A-B-C-F / A-D-E-F) violates the SRG,
    # so SRG protection must cost more than plain link-disjoint protection
    [ld] = solve(g, [("A", "F", 1)], "link_disjoint")
    total = lambda x: x.path_length(g, x.working) + x.path_length(g, x.backup)  # noqa: E731
    assert total(d) > total(ld)


def test_availability_model():
    g = grid()
    assert path_availability(g, ["A", "B", "C"], 0.1) == pytest.approx(0.9 * 0.9)
    d = RoutedDemand("A", "C", 1, ["A", "B", "C"], ["A", "D", "E", "F", "C"])
    aw, ab = 0.9 ** 2, 0.9 ** 4
    assert demand_availability(g, d, 0.1) == pytest.approx(1 - (1 - aw) * (1 - ab))


def test_srg_file_formats(tmp_path):
    f = tmp_path / "srg.txt"
    f.write_text("SRG1 (Munich, Berlin) (Hamburg, Frankfurt)\nSRG2 Bremen Hannover\n")
    a, b = read_srgs(f)
    assert a.links == [("Munich", "Berlin"), ("Hamburg", "Frankfurt")] and not a.nodes
    assert b.nodes == ["Bremen", "Hannover"] and not b.links


def test_real_dataset_solves():
    gp, dp, sp = dataset_paths("eu", "network_eu_b", "demand_eu_small")
    g = read_network(gp)
    routed = solve(g, read_demands(dp), "combined", read_srgs(sp))
    assert len(routed) == 6
    for d in routed:
        assert not set(d.working[1:-1]) & set(d.backup[1:-1])
