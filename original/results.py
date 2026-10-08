from input_data import *
from optimize_ilp import *
import numpy as np
import matplotlib.pyplot as plt
topos = ['network_eu_a', 'network_eu_b', 'network_eu_a_reduced', 'network_eu_b_increased']
# topos = ['network_eu_a_reduced']
# topos = ['cost266', 'nobel-eu']
# topos = ['cost266']
# demand = ['demand_eu_small']
demand = 'demand_eu_small'
SRG_name = 'srg_eu_links'

Unprotected = []
LinkDisjoint_work = []
LinkDisjoint_protect = []
NodeDisjoint_work = []
NodeDisjoint_protect = []
SRG_link_work = []
SRG_link_protect = []
Combine_work = []
Combine_protect = []

for network in topos:
    print('\n~~~~ %s ~~~~' % network)
    G = read_network(network)
    D = get_distance(G)
    R = read_demand(demand)
    SRG = read_SRG(SRG_name)
    # print "R"
    # print R['Madrid', 'Stockholm']
    print('~~~~ Unprotected paths ~~~~')
    distance, path = optimize_unprotected_path(G, D, R, network)

    print('~~~~ Link disjoint paths ~~~~')
    distance1, distance2, path1, path2 = optimize_link_disjoint(G, D, R, network)
    print path1
    print path2

    print('~~~~ Link SRG paths~~~~~')
    distance1_srg, distance2_srg, path1_srg, path2_srg = optimize_link_SRG(G, D, R, SRG, network)
    print path1_srg
    print path2_srg

    print('~~~~ Combine ~~~~~')
    distance1_combine, distance2_combine, path1_combine, path2_combine = optimize_combine(G, D, R, SRG, network)
    print path1_combine
    print path2_combine

    print('~~~~ Node disjoint paths~~~~~')
    distance1_node, distance2_node, path1_node, path2_node = optimize_node_disjoint(G, D, R, network)
    print path1_node
    print path2_node
    plt.ylabel('Average Availability [%]')
    plt.xlabel('Link Failure Probability [%/100km]')
    plt.title('Average availability for {}'.format(demand))
    fig = plt.figure()
    for r, dem in enumerate(R):
        src, dst = dem
        # print()
        print('~~~~~~~~~~~ Unprotected ~~~~~~~~~~~~~~~~~~~')
        print('Path length for (%s, %s) pair in unprotected case is: %.2f' % (src, dst, distance[r]))
        print('~~~~~~~~~~~ Link disjoint ~~~~~~~~~~~~~~~~')
        print('Working path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance1[r]))
        print('Backup path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance2[r]))
        print('~~~~~~~~~~ Node disjoint ~~~~~~~~~~~~~~~~')
        print('Working path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance1_node[r]))
        print('Backup path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance2_node[r]))
        print('~~~~~~~~~~ SRG  Link ~~~~~~~~~~~~~~~~')
        print('Working path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance1_srg[r]))
        print('Backup path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance2_srg[r]))
        print('~~~~~~~~~~ Combine ~~~~~~~~~~~~~~~~')
        print('Working path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance1_combine[r]))
        print('Backup path length for (%s, %s) pair in protected case is: %.2f' % (src, dst, distance2_combine[r]))

    Unprotected_count = []
    LinkDisjoint_work_count = []
    LinkDisjoint_protect_count =[]
    NodeDisjoint_work_count = []
    NodeDisjoint_protect_count =[]
    SRG_link_work_count =[]
    SRG_link_protect_count =[]
    Combine_work_count = []
    Combine_protect_count = []

    for r in range(0, len(distance)):
        Unprotected_count.append(distance[r])
        LinkDisjoint_work_count.append(distance1[r])
        LinkDisjoint_protect_count.append(distance2[r])
        NodeDisjoint_work_count.append(distance1_node[r])
        NodeDisjoint_protect_count.append(distance2_node[r])
        SRG_link_work_count.append(distance1_srg[r])
        SRG_link_protect_count.append(distance2_srg[r])
        Combine_work_count.append(distance1_combine[r])
        Combine_protect_count.append(distance2_combine[r])

    Unprotected.append(numpy.sum(Unprotected_count)/len(distance))
    LinkDisjoint_work.append(numpy.sum(LinkDisjoint_work_count)/len(distance))
    LinkDisjoint_protect.append(numpy.sum(LinkDisjoint_protect_count)/len(distance))
    NodeDisjoint_work.append(numpy.sum(NodeDisjoint_work_count)/len(distance))
    NodeDisjoint_protect.append(numpy.sum(NodeDisjoint_protect_count)/len(distance))
    SRG_link_work.append(numpy.sum(SRG_link_work_count)/len(distance))
    SRG_link_protect.append(numpy.sum(SRG_link_protect_count)/len(distance))
    Combine_work.append(numpy.sum(Combine_work_count)/len(distance))
    Combine_protect.append(numpy.sum(Combine_protect_count)/len(distance))


    # necessary variables
#
# fig = plt.figure()
ax = fig.add_subplot(111)

# the data
N = len(topos)
ind = np.arange(N)  # the x locations for the groups
width = 0.1  # the width of the bars
ax = fig.add_subplot(111)

# the bars
rects1 = ax.bar(ind, Unprotected, width, color='red')
rects2 = ax.bar(ind + width, LinkDisjoint_work, width, color='orange')
rects3 = ax.bar(ind + 2*width, NodeDisjoint_work, width, color='yellow')
rects4 = ax.bar(ind + 3*width, SRG_link_work, width, color='green')
rects5 = ax.bar(ind + 4*width, Combine_work, width, color='blue')
rects6 = ax.bar(ind + 5*width, LinkDisjoint_protect, width, color='purple')
rects7 = ax.bar(ind + 6*width, NodeDisjoint_protect, width, color='brown')
rects8 = ax.bar(ind + 7*width, SRG_link_protect, width, color='black')
rects9 = ax.bar(ind + 8*width, Combine_protect, width, color='grey')
# ax.set_ylim([1500,4000])
# axes and labels
ax.set_xlim(-width, len(ind) + width)
ax.set_ylim(1800, 4000)
ax.set_ylabel('Average path length [km]')
ax.set_title('Average path length for {}'.format(demand))
xTickMarks = ['network_eu_a', 'eu_b', 'eu_a_reduced', 'eu_b_increased']
ax.set_xticks(ind + width)
xtickNames = ax.set_xticklabels(xTickMarks)
# plt.setp(xtickNames, rotation=45, fontsize=10)

# add a legend
ax.legend((rects1[0], rects2[0], rects3[0], rects4[0], rects5[0], rects6[0], rects7[0], rects8[0], rects9[0]),
          ('Unprotected', 'LD_work', 'ND_work', 'SRG_work', 'combine_work', 'LD_protect',  'ND_protect', 'SRG_protect', 'combine_protect'))
plt.show()