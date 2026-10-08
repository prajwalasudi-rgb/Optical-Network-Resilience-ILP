import os
import matplotlib.pyplot as plt
import networkx as nx
# import re
from geopy.distance import vincenty
from mpl_toolkits.basemap import Basemap

# Get link length from node coordinates
def get_distance(g):
    for src, dst in g.edges():
        p1 = (g.node[src]['Latitude'], g.node[src]['Longitude'])
        p2 = (g.node[dst]['Latitude'], g.node[dst]['Longitude'])
        len = vincenty(p1, p2).meters / 1000
        g[src][dst]["weight"] = round(len, 2)

    dist = nx.all_pairs_dijkstra_path_length(g)
    d = {}
    for src in g.nodes():
        for dst in g.nodes():
            d[(src, dst)] = dist[src][dst]
    return d

# Average node degree
def average_degree(G):
    node_list = G.nodes()
    deg = list(G.degree(G.nodes()).values())
    return sum(deg)/len(deg)

# Read network
def read_network(name):
    topo = name + '.graphml'
    g = nx.read_graphml(topo)
    return g

# Read demands
def read_demand(name):
    filename = name + '.txt'
    fp = open(filename)
    lines = fp.readlines()

    # Read demands from file in the format
    # "source" "destination" "capacity"
    R = {}
    for line in lines:
        src, dst, cap = line.split()
        R[(src, dst)] = int(cap)
    fp.close()
    return R

def read_SRG(name):
    filename = name + '.txt'
    fp = open(filename)
    lines = fp.readlines()

    # Read demands from file in the format
    # "source" "destination" "capacity"
    SRG = []
    i = 0
    for line in lines:
        line = line.replace('(', ' ')
        line = line.replace(')', ' ')
        line = line.replace(',', '')
        headline, src1, dst1, src2, dst2 = line.split()
        # print headline
        # print src1
        # print dst1
        # print src2
        # print dst2
        SRG.append([])
        SRG[i].append(src1)
        SRG[i].append(dst1)
        SRG[i].append(src2)
        SRG[i].append(dst2)
        i = i+1
        # src, dst, cap = line.split()
        # R[(src, dst)] = int(cap)
    fp.close()
    return SRG




# Plot the network
def plot_network(g):
    plt.figure(figsize=(10,10))

    # Get the coordinates to plot the data
    m = Basemap(llcrnrlon=-12,llcrnrlat=30,
             urcrnrlon=32,urcrnrlat=65,
             resolution='i',area_thresh=500.0,projection='lcc',
             lat_0=42.0,lon_0=22.0)
    pos = {}
    for n in g.nodes():
        lon = g.node[n]['Longitude']
        lat = g.node[n]['Latitude']
        pos[n] = m(lon,lat)

    # Plot network nodes and edges
    nx.draw_networkx_nodes(g, pos, node_color='lightblue', node_size=200)
    nx.draw_networkx_edges(g,pos)

    # Plot node labels above the the nodes
    offset = 60000
    pos_labels = {}
    keys = pos.keys()
    for key in keys:
        x, y = pos[key]
        pos_labels[key] = (x, y+offset)

    nx.draw_networkx_labels(g,pos=pos_labels)

    # Plot country and coast lines
    m.drawcountries(linewidth=0.3)
    m.drawcoastlines(linewidth=0.2)
    plt.axis('off')
    plt.savefig('network.png')
    plt.show()

# Test input data
def test_input(netwrok, demand):
    print('\n~~~~ %s ~~~~' % netwrok)
    G = read_network(netwrok)
    print('Number of nodes: %d' % G.number_of_nodes())
    print('Number of links: %d' % G.number_of_edges())
    print('Average degree: %.2f' % average_degree(G))

    print('\n~~~~ %s ~~~~' % demand)
    R = read_demand(demand)
    for (src, dst) in R:
        print(src, dst, R[(src, dst)])

    plot_network(G)


network = 'cost266'
demand = 'demand_eu_big'
# test_input(network, demand)


