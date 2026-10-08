from gurobipy import *
import random
import numpy
from numpy import matrix
import matplotlib.pyplot as plt

# Optimize resilience
def optimize_unprotected_path(G, D, R, network):

    model = Model("Unprotected paths")

    # Identify the source and the destination of the demand
    # do nothing
    t = {}
    for r, (src, dst) in enumerate(R):
        for n in G.nodes():
            if n==src:
                t[r,n] = -1
            elif n==dst:
                t[r,n] = 1
            else:
                t[r,n] = 0

    # Transform undirected edges to directed arcs
    # do nothing
    d = {}
    arcs = []
    for i, j in G.edges():
        d[i,j] = D[i,j]
        d[j,i] = D[j,i]
        arcs.append((i,j))
        arcs.append((j,i))

    # Binary variables indicate if arc (i,j) belongs to the path of demand r
    # do nothing
    u= {}
    for r in range(len(R)):
        for i,j in arcs:
            u[r,i,j] = model.addVar(obj=0, vtype="B", name="u[%s,%s,%s]" %(r,i,j))
    model.update()

    # Optimization goal is to minimize the length of the paths
    # nothing
    model.setObjective(quicksum(u[r,i,j] * d[i,j] for r in range(len(R)) for i,j in arcs), GRB.MINIMIZE)

    # Flow conservation constraint
    # nothing
    for r in range(len(R)):
        for m in G.nodes():
            model.addConstr(quicksum(u[r,i,j] for i,j in arcs if j==m) - quicksum(u[r,i,j] for i,j in arcs if i==m), "=", t[r,m])

    # Start optimization
    model.params.outputflag = 0
    model.optimize()

    # If optimal solution is found get the results
    if model.status != GRB.Status.OPTIMAL:
        exit(1)
    else:
        su = model.getAttr('x', u)

    # Availability

    # Utilization
    # The result is given as set of paths for every demand
    distance = {}
    path = {}

    # availability = numpy.ones(len(R))
    distance_each_path = []
    foo = [0.0025, 0.005, 0.01, 0.2]
    for r in range(len(R)):
        p = []
        distance_each_path.append([])
        dp = 0
        for i,j in arcs:
            if su[r,i,j]>0:
                p.append((i,j))
                # print su[r,i,j]
                dp += d[i,j]
                distance_each_path[r].append(d[i,j])
                # print d[i, j]
                # fail = random.choice(foo)
                # fail = numpy.random.uniform(0.00005, 0.00025)
                # availability[r] = availability[r] * (1 - fail * d[i, j])

        # print ('Availability of {} demand is {}'.format(r + 1, availability[r]))
        distance[r] = dp
        path[r] = p

    ######################### Availability Begin####################
    fail = [0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2]
    availability_un = numpy.zeros(len(fail))
    # availability_1to1 = numpy.zeros(len(fail))
    # availability_1plus1 = numpy.zeros(len(fail))

    for z in range(0, len(fail)):
        # availability_2nd = numpy.ones(len(R))
        availability = numpy.ones(len(R))
        for x in range(0, len(R)):
            for y in range(0, len(path[x])):
                 #print len(path[x])
                 #print distance_each_path[x][y]
                 # fail = random.choice(foo)
                 # fail = numpy.random.uniform(0, 0.2)
                 availability[x] = availability[x] * (1 - fail[z] * distance_each_path[x][y] / 100)
                 # print ('Availability of {} demand is {}'.format(x+1, availability[x]))
        availability_un[z] = numpy.sum(availability)/len(R)
        print ('Average availability of unprotected path is %f' % availability_un[z])
    # print ('2nd version is %f' % (numpy.sum(availability_2nd)/len(R)))

    plt.plot(numpy.multiply(fail, 100), availability_un, label='Unprotected:' + str(network))
    plt.legend()
    ####################### Availability End ##########################

    ####################### Utilization Begin #########################
    # print arcs
    utilization = {}
    for i, j in arcs:
        utilization[(i, j)] = 0
    # print utilization

    demand_value = numpy.zeros(len(R))
    for r, (src, dst) in enumerate(R):
        demand_value[r] = R[(src, dst)]
    # print "demand_value"
    # print demand_value
    for r in range(0, len(R)):
        for i, j in arcs:
            if su[r, i, j] > 0:
                utilization[(i, j)] = utilization[(i, j)] + su[r, i, j] * demand_value[r]
    print ("utilization")
    print utilization


    total_utilization = 0
    total_links = 0
    for i,j in arcs:
        total_links += 1
        total_utilization = total_utilization + utilization[(i, j)]

    total_links /= 2
    average_utilization = total_utilization/total_links
    maximm = max(utilization,key=lambda  i:utilization[i])
    print ('max_utilization is ',  utilization[maximm])

    print ('total_utilization is %d' % total_utilization)
    print ('average_utilization is %f ' % average_utilization)
    ####################### Utilization End #########################
    model.reset()
    return distance, path


# MILP formulation for link disjoint paths
def optimize_link_disjoint(G, D, R, network):

    model = Model("Link disjoint paths")

    # Identify the source and the destination of the demand
    t = {}
    for r, (src, dst) in enumerate(R):
        for n in G.nodes():
            if n==src:
                t[r,n] = -1
            elif n==dst:
                t[r,n] = 1
            else:
                t[r,n] = 0

    # Transform undirected edges to directed arcs
    d = {}
    arcs = []
    for i, j in G.edges():
        d[i,j] = D[i,j]
        d[j,i] = D[j,i]
        arcs.append((i,j))
        arcs.append((j,i))

    # # Binary variables indicate if arc (i,j) belongs to the working and backup paths of demand r
    # change for node disjoint
    u, v = {}, {}
    for r in range(len(R)):
        for i,j in arcs:
            u[r,i,j] = model.addVar(vtype="B", name="u[%s,%s,%s]" %(r,i,j))
            v[r,i,j] = model.addVar(vtype="B", name="v[%s,%s,%s]" %(r,i,j))
    model.update()

    # Optimization goal
    # change node disjoint
    model.setObjective(quicksum((u[r,i,j] + v[r,i,j])*d[i,j] for r in range(len(R)) for i,j in arcs), GRB.MINIMIZE)

    # Constraint: Link paths have to be link disjoint
    # change constraint
    for r in range(len(R)):
        for i,j in arcs:
            model.addConstr(u[r,i,j] + v[r,i,j], "<=", 1, name="Link disjoint paths")

    # Flow conservation constraint
    for r in range(len(R)):
        for m in G.nodes():
            model.addConstr(quicksum(u[r,i,j] for i,j in arcs if j==m) - quicksum(u[r,i,j] for i,j in arcs if i==m), "=", t[r,m])
            model.addConstr(quicksum(v[r,i,j] for i,j in arcs if j==m) - quicksum(v[r,i,j] for i,j in arcs if i==m), "=", t[r,m])

    # Start optimization
    model.params.outputflag = 0
    model.optimize()

    # If optimal solution is found get the results
    if model.status != GRB.Status.OPTIMAL:
        print('Optimal solution is not found! The model is unfeasible or unbounded')
        exit(1)
    else:
        su = model.getAttr('x', u)
        sv = model.getAttr('x', v)


    # The result is given as set of working and protection paths for every demand
    distance1, distance2 = {}, {}
    path1, path2 = {}, {}
    distance_each_path1 = []
    distance_each_path2 = []
    for r in range(len(R)):
        d1=0
        d2=0
        distance_each_path1.append([])
        distance_each_path2.append([])
        p1 = []
        p2 = []
        for i,j in arcs:
            if su[r,i,j]>0:
                p1.append((i,j))
                d1 += d[i,j]
                distance_each_path1[r].append(d[i, j])
            if sv[r,i,j]>0:
                p2.append((i,j))
                d2 += d[i,j]
                distance_each_path2[r].append(d[i, j])

    # Select the shorter path as working path and longer as backup path
        if d1 <= d2:
            distance1[r] = d1
            distance2[r] = d2
            distance_each_path1[r] = distance_each_path1[r]
            distance_each_path2[r] = distance_each_path2[r]
            path1[r] = p1
            path2[r] = p2
            short = su
            long = sv
        else:
            distance1[r] = d2
            distance2[r] = d1
            temp = distance_each_path2[r]
            distance_each_path2[r] = distance_each_path1[r]
            distance_each_path1[r] = temp
            path1[r] = p2
            path2[r] = p1
            short = sv
            long = su

    # ######################### Availability Begin####################
    ######################### Availability Begin####################
    fail = [0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2]
    availability_1to1 = numpy.zeros(len(fail))
    availability_1plus1 = numpy.zeros(len(fail))

    for z in range(0, len(fail)):
        availability = numpy.ones(len(R))
        availability_21 = numpy.ones(len(R))
        availability_22 = numpy.ones(len(R))
        availability2 = numpy.ones(len(R))
        for x in range(0, len(R)):
            availability_21[x] = (1-fail[z]) ** (distance1[x]/100)
            for y in range(0, len(path1[x])):
                    # print len(path[x])
                    # print distance_each_path[x][y]
                    availability[x] = availability[x] * (1 - fail[z] * distance_each_path1[x][y]/100)
            print ('Availability of working path of {} demand is {}'.format(x + 1, availability[x]))

        for x in range(0, len(R)):
            availability_22[x] = (1-fail[z]) ** (distance2[x]/100)
            for y in range(0, len(path2[x])):
                    # print len(path[x])
                    # print distance_each_path[x][y]
                availability2[x] = availability2[x] * (1 - fail[z] * distance_each_path2[x][y]/100)
            #  print ('Availability of protection path of {} demand is {}'.format(x + 1, availability2[x]))

        unavailability = numpy.zeros(len(R))
        avg_availability_2 = numpy.zeros(len(R))
        avg_availability = numpy.zeros(len(R))
        for x in range(0, len(R)):
            unavailability[x] = (1 - availability[x]) * (1 - availability2[x])
            avg_availability[x] = 1 - unavailability[x]
            avg_availability_2[x] = 1 - (1 - availability_22[x]) * (1 - availability_21[x])
        # print ('Average availability of link disjoint is %f' % ((numpy.sum(availability) + numpy.sum(availability2))/len(R)))

        availability_1to1[z] = numpy.sum(avg_availability)/len(R)
        availability_1plus1[z] = numpy.sum(avg_availability)/len(R)
        print ('Average availability of link disjoint 1:1 is %f' % availability_1to1[z])
        print ('Average availability of link disjoint 1+1 is %f' % availability_1plus1[z])

    plt.plot(numpy.multiply(fail, 100), availability_1plus1, label='Link disjoint 1+1:'+str(network))
    plt.plot(numpy.multiply(fail, 100), availability_1to1, label='Link disjoint 1:1:'+str(network))
    plt.legend()




    # print ('2nd version is %f' %(numpy.mean(avg_availability_2)))
    ####################### Availability End ##########################

    # fail = 0.05
    # availability = numpy.ones(len(R))
    # availability_21 = numpy.ones(len(R))
    # availability_22 = numpy.ones(len(R))
    # availability2 = numpy.ones(len(R))
    # for x in range(0, len(R)):
    #     availability_21[x] = (1-fail) ** (distance1[x]/100)
    #     for y in range(0, len(path1[x])):
    #             # print len(path[x])
    #             # print distance_each_path[x][y]
    #             availability[x] = availability[x] * (1 - fail * distance_each_path1[x][y]/100)
    #     print ('Availability of working path of {} demand is {}'.format(x + 1, availability[x]))
    #
    # for x in range(0, len(R)):
    #     availability_22[x] = (1-fail) ** (distance2[x]/100)
    #     for y in range(0, len(path2[x])):
    #             # print len(path[x])
    #             # print distance_each_path[x][y]
    #         availability2[x] = availability2[x] * (1 - fail * distance_each_path2[x][y]/100)
    #     #  print ('Availability of protection path of {} demand is {}'.format(x + 1, availability2[x]))
    #
    # unavailability = numpy.zeros(len(R))
    # avg_availability_2 = numpy.zeros(len(R))
    # avg_availability = numpy.zeros(len(R))
    # for x in range(0, len(R)):
    #     unavailability[x] = (1 - availability[x]) * (1 - availability2[x])
    #     avg_availability[x] = 1 - unavailability[x]
    #     avg_availability_2[x] = 1 - (1 - availability_22[x]) * (1 - availability_21[x])
    # # print ('Average availability of link disjoint is %f' % ((numpy.sum(availability) + numpy.sum(availability2))/len(R)))
    # print ('Average availability of link disjoint 1:1 is %f' % (numpy.sum(avg_availability)/len(R)))
    # print ('Average availability of link disjoint 1+1 is %f' % (numpy.sum(avg_availability) / len(R)))
    # # print ('2nd version is %f' %(numpy.mean(avg_availability_2)))
    # ####################### Availability End ##########################

    ####################### Utilization Begin #########################
        # print arcs
    utilization = {}
    utilization2 = {}
    for i, j in arcs:
            utilization[(i, j)] = 0
            utilization2[(i, j)] = 0

    demand_value = numpy.zeros(len(R))
    for r, (src, dst) in enumerate(R):
        demand_value[r] = R[(src, dst)]
        # print "demand_value"
        # print demand_value
    for r in range(0, len(R)):
        for i, j in arcs:
            if short[r, i, j] > 0:
                utilization[(i, j)] = utilization[(i, j)] + demand_value[r]
            if long[r, i, j] > 0:
                utilization2[(i, j)] = utilization2[(i, j)] + demand_value[r]
    total_utilization = 0
    total_utilization2 = 0
    total_links = 0
    print ("utilization")
    print utilization
    print ("utilization2")
    print utilization2
    for i, j in arcs:
        total_links += 1
        total_utilization = total_utilization + utilization[(i, j)]
        total_utilization2 = total_utilization2 + utilization2[(i, j)]

    total_links /= 2
    average_utilization = total_utilization / total_links
    average_utilization2 = total_utilization2 / total_links
    maximm = max(utilization, key=lambda i: utilization[i])
    print ('max_utilization 1:1 is ', utilization[maximm])
    maximm2 = max(utilization2, key=lambda i: utilization2[i])
    print ('max_utilization 1+1 is ', utilization2[maximm2])
    # print ('total_utilization of working path is %d' % total_utilization)
    print ('1:1 average_utilization of working path is %f ' % average_utilization)
    # print ('average_utilization of protection path is %f ' % average_utilization2)
    print ('1+1 average_utilization in total is %f ' % (average_utilization2 + average_utilization))
    ####################### Utilization End #########################
    model.reset()
    return distance1, distance2, path1, path2

def optimize_node_disjoint(G, D, R, network):

    model = Model("Node disjoint paths")

    # Identify the source and the destination of the demand
    t = {}
    for r, (src, dst) in enumerate(R):
        for n in G.nodes():
            if n==src:
                t[r,n] = -1
            elif n==dst:
                t[r,n] = 1
            else:
                t[r,n] = 0

    # Transform undirected edges to directed arcs
    d = {}
    arcs = []
    for i, j in G.edges():
        d[i,j] = D[i,j]
        d[j,i] = D[j,i]
        arcs.append((i,j))
        arcs.append((j,i))

    # # Binary variables indicate if arc (i,j) belongs to the working and backup paths of demand r
    # change for node disjoint
    u, v = {}, {}
    node_u = {}
    node_v = {}
    for r in range(len(R)):
        for i, j in arcs:
            u[r,i,j] = model.addVar(vtype="B", name="u[%s,%s,%s]" %(r,i,j))
            v[r,i,j] = model.addVar(vtype="B", name="v[%s,%s,%s]" %(r,i,j))
    model.update()


    for r in range(len(R)):
        for i in G.nodes():
            node_u[r, i] = model.addVar(vtype="B", name="node_u[%s,%s]" % (r, i))
            node_v[r, i] = model.addVar(vtype="B", name="node_v[%s,%s]" % (r, i))
    model.update()


    #print node_u.X

    # for de in range(0, len(R)):
    #     for i, j in arcs:
    #         node_u = model.addVar(vtype="B", name="u[%s,%s]" % (de, i))
    #         node_v = model.addVar(vtype="B", name="u[%s,%s]" % (de, i))
    # model.update()
    #
    # print ('node_u is {}'.format(node_u))
    # print ('node_v is {}'.format(node_v))

    # Optimization goal minimize distance
    # change node disjoint
    model.setObjective(quicksum((u[r,i,j] + v[r,i,j])*d[i,j] for r in range(len(R)) for i,j in arcs), GRB.MINIMIZE)
    # model.setObjective(quicksum(node_u[r, i] + node_v[r, i] for r in range(len(R)) for i in G.nodes()), GRB.MINIMIZE)


    # Constraint: Link paths have to be link disjoint
    # change constraint
    # for r in range(len(R)):
    #     for i, j in arcs:
    #         for x, y in arcs:
    #             if (i, y) in arcs:
    #                 model.addConstr( u[r, i, y] + v[r, i, y] , "<=", 1, name="Node disjoint paths")
    #             elif (x, i) in arcs:
    #                  model.addConstr(u[r, x, i] + v[r, x, i], "<=", 1, name="Node disjoint paths")
    #             elif (x, j) in arcs:
    #                  model.addConstr(u[r, x, j] + v[r, x, j], "<=", 1, name="Node disjoint paths")
    #             elif (j, y) in arcs:
    #                  model.addConstr(u[r, j, y] + v[r, j, y], "<=", 1, name="Node disjoint paths")


    # for r in range(len(R)):
    #     for n in G.edges():
    #         sum = 0
    #         for i, j in G.edges():
    #             if i == n:
    #                 sum = sum + u[r, n, j] + v[r, n, j] + u[r, i, n] + v[r, i, n]
    #         model.addConstr(sum, "<=", 1, name="Node disjoint")
    for r in range(len(R)):
        for i, j in arcs:
            model.addConstr(u[r, i, j] + v[r, i, j], "<=", 1, name="Link disjoint paths")
            # model.addConstr(node_u[r, i] + node_v[r, i], "<=", 1, name="Link disjoint paths")
    # Flow conservation constraint
    used_node = []
    # TODO ask tutors about constraints
    for r in range(len(R)):
        for m in G.nodes():
            model.addConstr(quicksum(u[r, i, j] for i, j in arcs if j == m) - quicksum(u[r, i, j] for i, j in arcs if i == m),"=", t[r, m])
            model.addConstr(quicksum(v[r, i, j] for i, j in arcs if j == m) - quicksum(v[r, i, j] for i, j in arcs if i == m),"=", t[r, m])


    # Constraint: Path have to be node disjoint
    for r in range(len(R)):
        for m in G.nodes():
            if t[r, m] == 0:
                model.addConstr(node_u[r, m] + node_v[r, m], "<=", 1, name="Node disjoint paths")


    for r in range(len(R)):
        for m in G.nodes():
            model.addConstr(node_u[r, m], "=", quicksum(u[r, i, j] for i, j in arcs if i == m)) # change afterwards, something misssing
            model.addConstr(node_v[r, m], "=", quicksum(v[r, i, j] for i, j in arcs if i == m))

    # for r in range(len(R)):
    #     for i, j in arcs:
    #         for k, l in arcs:
    #                 if (i == k) or (i == l) or (j == k) or (j == l):
    #                     model.addConstr(u[r, i, j] + v[r, k, l], "<=", 1, name="Node disjoint paths")




    # Start optimization
    model.params.outputflag = 0
    model.optimize()

    # If optimal solution is found get the results
    if model.status != GRB.Status.OPTIMAL:
        print('Optimal solution is not found! The model is unfeasible or unbounded')
        exit(1)
    else:
        su = model.getAttr('x',  u)
        sv = model.getAttr('x',  v)

####################### From Link disjoint ##################


    # The result is given as set of working and protection paths for every demand
    distance1, distance2 = {}, {}
    path1, path2 = {}, {}
    distance_each_path1 = []
    distance_each_path2 = []
    for r in range(len(R)):
        d1 = 0
        d2 = 0
        distance_each_path1.append([])
        distance_each_path2.append([])
        p1 = []
        p2 = []
        for i, j in arcs:
            if su[r, i, j] > 0:
                p1.append((i, j))
                d1 += d[i, j]
                distance_each_path1[r].append(d[i, j])
            if sv[r, i, j] > 0:
                p2.append((i, j))
                d2 += d[i, j]
                distance_each_path2[r].append(d[i, j])
                # Select the shorter path as working path and longer as backup path
        if d1 <= d2:
            distance1[r] = d1
            distance2[r] = d2
            distance_each_path1[r] = distance_each_path1[r]
            distance_each_path2[r] = distance_each_path2[r]
            path1[r] = p1
            path2[r] = p2
            short = su
            long = sv
        else:
            distance1[r] = d2
            distance2[r] = d1
            temp = distance_each_path2[r]
            distance_each_path2[r] = distance_each_path1[r]
            distance_each_path1[r] = temp
            path1[r] = p2
            path2[r] = p1
            short = sv
            long = su

    ######################### Availability Begin####################
    ########################## Availability Begin####################
    fail = [0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2]
    availability_1to1 = numpy.zeros(len(fail))
    availability_1plus1 = numpy.zeros(len(fail))

    for z in range(0, len(fail)):
        availability = numpy.ones(len(R))
        availability_21 = numpy.ones(len(R))
        availability_22 = numpy.ones(len(R))
        availability2 = numpy.ones(len(R))
        for x in range(0, len(R)):
            availability_21[x] = (1-fail[z]) ** (distance1[x]/100)
            for y in range(0, len(path1[x])):
                    # print len(path[x])
                    # print distance_each_path[x][y]
                    availability[x] = availability[x] * (1 - fail[z] * distance_each_path1[x][y]/100)
            print ('Availability of working path of {} demand is {}'.format(x + 1, availability[x]))

        for x in range(0, len(R)):
            availability_22[x] = (1-fail[z]) ** (distance2[x]/100)
            for y in range(0, len(path2[x])):
                    # print len(path[x])
                    # print distance_each_path[x][y]
                availability2[x] = availability2[x] * (1 - fail[z] * distance_each_path2[x][y]/100)
            #  print ('Availability of protection path of {} demand is {}'.format(x + 1, availability2[x]))

        unavailability = numpy.zeros(len(R))
        avg_availability_2 = numpy.zeros(len(R))
        avg_availability = numpy.zeros(len(R))
        for x in range(0, len(R)):
            unavailability[x] = (1 - availability[x]) * (1 - availability2[x])
            avg_availability[x] = 1 - unavailability[x]
            avg_availability_2[x] = 1 - (1 - availability_22[x]) * (1 - availability_21[x])
        # print ('Average availability of link disjoint is %f' % ((numpy.sum(availability) + numpy.sum(availability2))/len(R)))

        availability_1to1[z] = numpy.sum(avg_availability)/len(R)
        availability_1plus1[z] = numpy.sum(avg_availability)/len(R)
        print ('Average availability of node disjoint 1:1 is %f' % availability_1to1[z])
        print ('Average availability of node disjoint 1+1 is %f' % availability_1plus1[z])

    plt.plot(numpy.multiply(fail, 100), availability_1plus1, label='Node disjoint 1+1:'+str(network))
    plt.plot(numpy.multiply(fail, 100), availability_1to1, label='Node disjoint 1:1:'+str(network))
    plt.legend()




    # print ('2nd version is %f' %(numpy.mean(avg_availability_2)))
    ####################### Availability End ##########################
    # fail = 0.05
    # availability = numpy.ones(len(R))
    # availability_21 = numpy.ones(len(R))
    # availability_22 = numpy.ones(len(R))
    # availability2 = numpy.ones(len(R))
    # for x in range(0, len(R)):
    #     availability_21[x] = (1 - fail) ** (distance1[x] / 100)
    #     for y in range(0, len(path1[x])):
    #         # print len(path[x])
    #         # print distance_each_path[x][y]
    #         availability[x] = availability[x] * (1 - fail * distance_each_path1[x][y] / 100)
    #     print ('Availability of working path of {} demand is {}'.format(x + 1, availability[x]))
    #
    # for x in range(0, len(R)):
    #     availability_22[x] = (1 - fail) ** (distance2[x] / 100)
    #     for y in range(0, len(path2[x])):
    #         # print len(path[x])
    #         # print distance_each_path[x][y]
    #         availability2[x] = availability2[x] * (1 - fail * distance_each_path2[x][y] / 100)
    #         #  print ('Availability of protection path of {} demand is {}'.format(x + 1, availability2[x]))
    #
    # unavailability = numpy.zeros(len(R))
    # avg_availability_2 = numpy.zeros(len(R))
    # avg_availability = numpy.zeros(len(R))
    # for x in range(0, len(R)):
    #     unavailability[x] = (1 - availability[x]) * (1 - availability2[x])
    #     avg_availability[x] = 1 - unavailability[x]
    #     avg_availability_2[x] = 1 - (1 - availability_22[x]) * (1 - availability_21[x])
    # # print ('Average availability of link disjoint is %f' % ((numpy.sum(availability) + numpy.sum(availability2))/len(R)))
    # print ('Average availability of link disjoint 1:1 is %f' % (numpy.sum(avg_availability) / len(R)))
    # print ('Average availability of link disjoint 1+1 is %f' % (numpy.sum(avg_availability) / len(R)))
    # # print ('2nd version is %f' %(numpy.mean(avg_availability_2)))
    # ####################### Availability End ##########################

    ####################### Utilization Begin #########################
    # print arcs
    utilization = {}
    utilization2 = {}
    for i, j in arcs:
        utilization[(i, j)] = 0
        utilization2[(i, j)] = 0

    demand_value = numpy.zeros(len(R))
    for r, (src, dst) in enumerate(R):
        demand_value[r] = R[(src, dst)]
        # print "demand_value"
        # print demand_value
    for r in range(0, len(R)):
        for i, j in arcs:
            if short[r, i, j] > 0:
                utilization[(i, j)] = utilization[(i, j)] + demand_value[r]
            if long[r, i, j] > 0:
                utilization2[(i, j)] = utilization2[(i, j)] + demand_value[r]

    print ("utilization")
    print utilization
    print ("utilization2")
    print utilization2
    total_utilization = 0
    total_utilization2 = 0
    total_links = 0
    for i, j in arcs:
        total_links += 1
        total_utilization = total_utilization + utilization[(i, j)]
        total_utilization2 = total_utilization2 + utilization2[(i, j)]

    total_links /= 2
    average_utilization = total_utilization / total_links
    average_utilization2 = total_utilization2 / total_links
    maximm = max(utilization, key=lambda i: utilization[i])
    print ('max_utilization 1:1 is ', utilization[maximm])
    maximm2 = max(utilization2, key=lambda i: utilization2[i])
    print ('max_utilization 1+1 is ', utilization2[maximm2])
    print ('1:1 average_utilization of working path is %f ' % average_utilization)
    print ('1+1 average_utilization in total is %f ' % (average_utilization2 + average_utilization))
    ####################### Utilization End #########################
    model.reset()
    return distance1, distance2, path1, path2

def optimize_link_SRG(G, D, R, SRG, network):

    model = Model("Link SRG paths")

    # Identify the source and the destination of the demand
    t = {}
    for r, (src, dst) in enumerate(R):
        for n in G.nodes():
            if n==src:
                t[r,n] = -1
            elif n==dst:
                t[r,n] = 1
            else:
                t[r,n] = 0

    # Transform undirected edges to directed arcs
    d = {}
    arcs = []
    for i, j in G.edges():
        d[i,j] = D[i,j]
        d[j,i] = D[j,i]
        arcs.append((i,j))
        arcs.append((j,i))

    # # Binary variables indicate if arc (i,j) belongs to the working and backup paths of demand r
    u, v = {}, {}
    for r in range(len(R)):
        for i,j in arcs:
            u[r,i,j] = model.addVar(vtype="B", name="u[%s,%s,%s]" %(r,i,j))
            v[r,i,j] = model.addVar(vtype="B", name="v[%s,%s,%s]" %(r,i,j))
    model.update()

    # Optimization goal
    # change node disjoint
    model.setObjective(quicksum((u[r,i,j] + v[r,i,j])*d[i,j] for r in range(len(R)) for i,j in arcs), GRB.MINIMIZE)

    # Constraint: Link paths have to be link disjoint
    # change constraint
    # TODO ask tutor for SRG constraints
    for r in range(len(R)):
        for i,j in arcs:
            model.addConstr(u[r, i, j] + v[r, i, j], "<=", 1, name="Link disjoint paths1")
        for src1, dst1, src2, dst2 in SRG:
            model.addConstr(u[r, src1, dst1] + u[r, dst1, src1] + v[r, src1, dst1] + v[r, dst1, src1], "<=", 1,
                            name="Link SRG paths1")
            model.addConstr(u[r, src1, dst1] + u[r, dst1, src1] + v[r, src2, dst2] + v[r, dst2, src2], "<=", 1,
                            name="Link SRG paths2")
            model.addConstr(u[r, src2, dst2] + u[r, dst2, src2] + v[r, src1, dst1] + v[r, dst1, src1], "<=", 1,
                            name="Link SRG paths3")
            model.addConstr(u[r, src2, dst2] + u[r, dst2, src2] + v[r, src2, dst2] + v[r, dst2, src2], "<=", 1,
                            name="Link SRG paths4")





            # model.addConstr(u[r, src1, dst1] + u[r, dst1, src1] + v[r, src1, dst1] + v[r, dst1, src1] + v[r, src2, dst2] + v[r, dst2, src2], "<=", 1, name="Link SRG paths")
            # model.addConstr(u[r, src2, dst2] + u[r, dst2, src2] + v[r, src1, dst1] + v[r, dst1, src1] + v[r, src2, dst2] + v[r, dst2, src2], "<=", 1, name="Link SRG paths")
            # model.addConstr(v[r, src1, dst1] + v[r, dst1, src1] + u[r, src1, dst1] + u[r, dst1, src1] + u[r, src2, dst2] + u[r, dst2, src2], "<=", 1, name="Link SRG paths")
            # model.addConstr(v[r, src2, dst2] + v[r, dst2, src2] + u[r, src1, dst1] + u[r, dst1, src1] + u[r, src2, dst2] + u[r, dst2, src2], "<=", 1, name="Link SRG paths")

            # model.addConstr(u[r, src1, dst1] + v[r, dst2, src2], "<=", 1, name="Link SRG paths")
            # model.addConstr(u[r, dst1, src1] + v[r, src2, dst2], "<=", 1, name="Link SRG paths")
            # model.addConstr(u[r, dst1, src1] + v[r, dst2, src2], "<=", 1, name="Link SRG paths")

    # Flow conservation constraint
    for r in range(len(R)):
        for m in G.nodes():
            model.addConstr(quicksum(u[r,i,j] for i,j in arcs if j==m) - quicksum(u[r,i,j] for i,j in arcs if i==m), "=", t[r,m])
            model.addConstr(quicksum(v[r,i,j] for i,j in arcs if j==m) - quicksum(v[r,i,j] for i,j in arcs if i==m), "=", t[r,m])

    # Start optimization
    model.params.outputflag = 0
    model.optimize()

    # If optimal solution is found get the results
    if model.status != GRB.Status.OPTIMAL:
        print('Optimal solution is not found! The model is unfeasible or unbounded')
        exit(1)
    else:
        su = model.getAttr('x', u)
        sv = model.getAttr('x', v)


    # The result is given as set of working and protection paths for every demand
    distance1, distance2 = {}, {}
    path1, path2 = {}, {}
    distance_each_path1 = []
    distance_each_path2 = []
    for r in range(len(R)):
        d1=0
        d2=0
        distance_each_path1.append([])
        distance_each_path2.append([])
        p1 = []
        p2 = []
        for i,j in arcs:
            if su[r,i,j]>0:
                p1.append((i,j))
                d1 += d[i,j]
                distance_each_path1[r].append(d[i, j])
            if sv[r,i,j]>0:
                p2.append((i,j))
                d2 += d[i,j]
                distance_each_path2[r].append(d[i, j])

    # Select the shorter path as working path and longer as backup path
        if d1 <= d2:
            distance1[r] = d1
            distance2[r] = d2
            distance_each_path1[r] = distance_each_path1[r]
            distance_each_path2[r] = distance_each_path2[r]
            path1[r] = p1
            path2[r] = p2
            short = su
            long = sv
        else:
            distance1[r] = d2
            distance2[r] = d1
            temp = distance_each_path2[r]
            distance_each_path2[r] = distance_each_path1[r]
            distance_each_path1[r] = temp
            path1[r] = p2
            path2[r] = p1
            short = sv
            long = su

    ######################### Availability Begin####################
    fail = [0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2]
    availability_1to1 = numpy.zeros(len(fail))
    availability_1plus1 = numpy.zeros(len(fail))

    for z in range(0, len(fail)):
        availability = numpy.ones(len(R))
        availability_21 = numpy.ones(len(R))
        availability_22 = numpy.ones(len(R))
        availability2 = numpy.ones(len(R))
        for x in range(0, len(R)):
            availability_21[x] = (1 - fail[z]) ** (distance1[x] / 100)
            for y in range(0, len(path1[x])):
                # print len(path[x])
                # print distance_each_path[x][y]
                availability[x] = availability[x] * (1 - fail[z] * distance_each_path1[x][y] / 100)
            print ('Availability of working path of {} demand is {}'.format(x + 1, availability[x]))

        for x in range(0, len(R)):
            availability_22[x] = (1 - fail[z]) ** (distance2[x] / 100)
            for y in range(0, len(path2[x])):
                # print len(path[x])
                # print distance_each_path[x][y]
                availability2[x] = availability2[x] * (1 - fail[z] * distance_each_path2[x][y] / 100)
                #  print ('Availability of protection path of {} demand is {}'.format(x + 1, availability2[x]))

        unavailability = numpy.zeros(len(R))
        avg_availability_2 = numpy.zeros(len(R))
        avg_availability = numpy.zeros(len(R))
        for x in range(0, len(R)):
            unavailability[x] = (1 - availability[x]) * (1 - availability2[x])
            avg_availability[x] = 1 - unavailability[x]
            avg_availability_2[x] = 1 - (1 - availability_22[x]) * (1 - availability_21[x])
        # print ('Average availability of link disjoint is %f' % ((numpy.sum(availability) + numpy.sum(availability2))/len(R)))

        availability_1to1[z] = numpy.sum(avg_availability) / len(R)
        availability_1plus1[z] = numpy.sum(avg_availability) / len(R)
        print ('Average availability of SRG link 1:1 is %f' % availability_1to1[z])
        print ('Average availability of SRG link 1+1 is %f' % availability_1plus1[z])

    plt.plot(numpy.multiply(fail, 100), availability_1plus1, label='SRG link 1+1:' + str(network))
    plt.plot(numpy.multiply(fail, 100), availability_1to1, label='SRG link 1:1:' + str(network))
    plt.legend()

    # print ('2nd version is %f' %(numpy.mean(avg_availability_2)))
    ####################### Availability End ##########################


    ####################### Utilization Begin #########################
        # print arcs
    utilization = {}
    utilization2 = {}
    for i, j in arcs:
            utilization[(i, j)] = 0
            utilization2[(i, j)] = 0

    demand_value = numpy.zeros(len(R))
    for r, (src, dst) in enumerate(R):
        demand_value[r] = R[(src, dst)]
        # print "demand_value"
        # print demand_value
    for r in range(0, len(R)):
        for i, j in arcs:
            if short[r, i, j] > 0:
                utilization[(i, j)] = utilization[(i, j)] + demand_value[r]
            if long[r, i, j] > 0:
                utilization2[(i, j)] = utilization2[(i, j)] + demand_value[r]
    total_utilization = 0
    total_utilization2 = 0
    total_links = 0
    for i, j in arcs:
        total_links += 1
        total_utilization = total_utilization + utilization[(i, j)]
        total_utilization2 = total_utilization2 + utilization2[(i, j)]
    print ("utilization")
    print utilization
    print ("utilization2")
    print utilization2
    total_links /= 2
    average_utilization = total_utilization / total_links
    average_utilization2 = total_utilization2 / total_links
    maximm = max(utilization, key=lambda i: utilization[i])
    print ('max_utilization 1:1 is ', utilization[maximm])
    maximm2 = max(utilization2, key=lambda i: utilization2[i])
    print ('max_utilization 1+1 is ', utilization2[maximm2])
    # print ('total_utilization of working path is %d' % total_utilization)
    print ('1:1 average_utilization of working path is %f ' % average_utilization)
    # print ('average_utilization of protection path is %f ' % average_utilization2)
    print ('1+1 average_utilization in total is %f ' % (average_utilization2 + average_utilization))
    ####################### Utilization End #########################
    model.reset()
    return distance1, distance2, path1, path2

def optimize_combine(G, D, R, SRG, network):

    model = Model("Link Combine")
    # Identify the source and the destination of the demand
    t = {}
    for r, (src, dst) in enumerate(R):
        for n in G.nodes():
            if n==src:
                t[r,n] = -1
            elif n==dst:
                t[r,n] = 1
            else:
                t[r,n] = 0

    # Transform undirected edges to directed arcs
    d = {}
    arcs = []
    for i, j in G.edges():
        d[i,j] = D[i,j]
        d[j,i] = D[j,i]
        arcs.append((i,j))
        arcs.append((j,i))

    # # Binary variables indicate if arc (i,j) belongs to the working and backup paths of demand r
    u, v = {}, {}
    node_u = {}
    node_v = {}
    for r in range(len(R)):
        for i,j in arcs:
            u[r,i,j] = model.addVar(vtype="B", name="u[%s,%s,%s]" %(r,i,j))
            v[r,i,j] = model.addVar(vtype="B", name="v[%s,%s,%s]" %(r,i,j))
    model.update()

    for r in range(len(R)):
        for i in G.nodes():
            node_u[r, i] = model.addVar(vtype="B", name="node_u[%s,%s]" % (r, i))
            node_v[r, i] = model.addVar(vtype="B", name="node_v[%s,%s]" % (r, i))
    model.update()

    # Optimization goal
    # change node disjoint
   # model.setObjective(quicksum(node_u[r, i] + node_v[r, i] for r in range(len(R)) for i in G.nodes()), GRB.MINIMIZE)
    model.setObjective(quicksum((u[r,i,j] + v[r,i,j])*d[i,j] for r in range(len(R)) for i,j in arcs), GRB.MINIMIZE)

    # Constraint: Link paths have to be link disjoint
    # change constraint
    # TODO ask tutor for SRG constraints
    for r in range(len(R)):
        for m in G.nodes():
            if t[r, m] == 0:
                model.addConstr(node_u[r, m] + node_v[r, m], "<=", 1, name="Node disjoint paths")
        for i, j in arcs:
            model.addConstr(u[r,i,j] + v[r,i,j], "<=", 1, name="Link disjoint paths")
        for src1, dst1, src2, dst2 in SRG:
            model.addConstr(u[r, src1, dst1] + u[r, dst1, src1] + v[r, src1, dst1] + v[r, dst1, src1], "<=", 1, name="Link SRG paths")
            model.addConstr(u[r, src1, dst1] + u[r, dst1, src1] + v[r, src2, dst2] + v[r, dst2, src2], "<=", 1, name="Link SRG paths")
            model.addConstr(u[r, src2, dst2] + u[r, dst2, src2] + v[r, src1, dst1] + v[r, dst1, src1], "<=", 1,
                            name="Link SRG paths")
            model.addConstr(u[r, src2, dst2] + u[r, dst2, src2] + v[r, src2, dst2] + v[r, dst2, src2], "<=", 1,
                            name="Link SRG paths")

    # Flow conservation constraint
    # Node disjoint
    # for r in range(len(R)):



    for r in range(len(R)):
        for m in G.nodes():
            model.addConstr(node_u[r, m], "=", quicksum(u[r, i, j] for i, j in arcs if i == m)) # change afterwards, something misssing
            model.addConstr(node_v[r, m], "=", quicksum(v[r, i, j] for i, j in arcs if i == m))

    for r in range(len(R)):
        for m in G.nodes():
            model.addConstr(quicksum(u[r,i,j] for i,j in arcs if j==m) - quicksum(u[r,i,j] for i,j in arcs if i==m), "=", t[r,m])
            model.addConstr(quicksum(v[r,i,j] for i,j in arcs if j==m) - quicksum(v[r,i,j] for i,j in arcs if i==m), "=", t[r,m])


    # Start optimization
    model.params.outputflag = 0
    model.optimize()

    # If optimal solution is found get the results
    if model.status != GRB.Status.OPTIMAL:
        print('Optimal solution is not found! The model is unfeasible or unbounded')
        exit(1)
    else:
        su = model.getAttr('x', u)
        sv = model.getAttr('x', v)


    # The result is given as set of working and protection paths for every demand
    distance1, distance2 = {}, {}
    path1, path2 = {}, {}
    distance_each_path1 = []
    distance_each_path2 = []
    for r in range(len(R)):
        d1=0
        d2=0
        distance_each_path1.append([])
        distance_each_path2.append([])
        p1 = []
        p2 = []
        for i,j in arcs:
            if su[r,i,j]>0:
                p1.append((i,j))
                d1 += d[i,j]
                distance_each_path1[r].append(d[i, j])
            if sv[r,i,j]>0:
                p2.append((i,j))
                d2 += d[i,j]
                distance_each_path2[r].append(d[i, j])

    # Select the shorter path as working path and longer as backup path
        if d1 <= d2:
            distance1[r] = d1
            distance2[r] = d2
            distance_each_path1[r] = distance_each_path1[r]
            distance_each_path2[r] = distance_each_path2[r]
            path1[r] = p1
            path2[r] = p2
            short = su
            long = sv
        else:
            distance1[r] = d2
            distance2[r] = d1
            temp = distance_each_path2[r]
            distance_each_path2[r] = distance_each_path1[r]
            distance_each_path1[r] = temp
            path1[r] = p2
            path2[r] = p1
            short = sv
            long = su

    ######################### Availability Begin####################
    fail = [0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2]
    availability_1to1 = numpy.zeros(len(fail))
    availability_1plus1 = numpy.zeros(len(fail))

    for z in range(0, len(fail)):
        availability = numpy.ones(len(R))
        availability_21 = numpy.ones(len(R))
        availability_22 = numpy.ones(len(R))
        availability2 = numpy.ones(len(R))
        for x in range(0, len(R)):
            availability_21[x] = (1-fail[z]) ** (distance1[x]/100)
            for y in range(0, len(path1[x])):
                    # print len(path[x])
                    # print distance_each_path[x][y]
                    availability[x] = availability[x] * (1 - fail[z] * distance_each_path1[x][y]/100)
            print ('Availability of working path of {} demand is {}'.format(x + 1, availability[x]))

        for x in range(0, len(R)):
            availability_22[x] = (1-fail[z]) ** (distance2[x]/100)
            for y in range(0, len(path2[x])):
                    # print len(path[x])
                    # print distance_each_path[x][y]
                availability2[x] = availability2[x] * (1 - fail[z] * distance_each_path2[x][y]/100)
            #  print ('Availability of protection path of {} demand is {}'.format(x + 1, availability2[x]))

        unavailability = numpy.zeros(len(R))
        avg_availability_2 = numpy.zeros(len(R))
        avg_availability = numpy.zeros(len(R))
        for x in range(0, len(R)):
            unavailability[x] = (1 - availability[x]) * (1 - availability2[x])
            avg_availability[x] = 1 - unavailability[x]
            avg_availability_2[x] = 1 - (1 - availability_22[x]) * (1 - availability_21[x])
        # print ('Average availability of link disjoint is %f' % ((numpy.sum(availability) + numpy.sum(availability2))/len(R)))

        availability_1to1[z] = numpy.sum(avg_availability)/len(R)
        availability_1plus1[z] = numpy.sum(avg_availability)/len(R)
        print ('Average availability of combination 1:1 is %f' % availability_1to1[z])
        print ('Average availability of combination 1+1 is %f' % availability_1plus1[z])

    plt.plot(numpy.multiply(fail, 100), availability_1plus1, label='Combine 1+1:'+str(network))
    plt.plot(numpy.multiply(fail, 100), availability_1to1, label='Combine 1:1:'+str(network))
    plt.legend()




    # print ('2nd version is %f' %(numpy.mean(avg_availability_2)))
    ####################### Availability End ##########################

    ####################### Utilization Begin #########################
        # print arcs
    utilization = {}
    utilization2 = {}
    for i, j in arcs:
            utilization[(i, j)] = 0
            utilization2[(i, j)] = 0

    demand_value = numpy.zeros(len(R))
    for r, (src, dst) in enumerate(R):
        demand_value[r] = R[(src, dst)]
        # print "demand_value"
        # print demand_value
    for r in range(0, len(R)):
        for i, j in arcs:
            if short[r, i, j] > 0:
                utilization[(i, j)] = utilization[(i, j)] + demand_value[r]
            if long[r, i, j] > 0:
                utilization2[(i, j)] = utilization2[(i, j)] + demand_value[r]
    total_utilization = 0
    total_utilization2 = 0
    total_links = 0
    for i, j in arcs:
        total_links += 1
        total_utilization = total_utilization + utilization[(i, j)]
        total_utilization2 = total_utilization2 + utilization2[(i, j)]
    print ("utilization")
    print utilization
    print ("utilization2")
    print utilization2
    total_links /= 2
    average_utilization = total_utilization / total_links
    average_utilization2 = total_utilization2 / total_links
    # print ('total_utilization of working path is %d' % total_utilization)
    maximm = max(utilization, key=lambda i: utilization[i])
    print ('max_utilization 1:1 is ', utilization[maximm])
    maximm2 = max(utilization2, key=lambda i: utilization2[i])
    print ('max_utilization 1+1 is ', utilization2[maximm2])
    print ('1:1 average_utilization of working path is %f ' % average_utilization)
    # print ('average_utilization of protection path is %f ' % average_utilization2)
    print ('1+1 average_utilization in total is %f ' % (average_utilization2 + average_utilization))
    ####################### Utilization End #########################
    model.reset()
    return distance1, distance2, path1, path2




