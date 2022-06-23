from gurobipy import *
import argparse
from datetime import datetime
import pandas as pd
import numpy as np
import sys 

# read input args
# new_ilp.py B(cost) eta clusters input_file
parser=argparse.ArgumentParser()
parser.add_argument('objective', type=str, help = "'MAX' = maximize items covered (set 'eta' = 0), 'MIN' = minimize tags used (set 'B' = 0)")
parser.add_argument('B', type=int, help = 'cost (maximum total tags allowed)')
parser.add_argument('eta', type=int, help = 'minimum number of objects covered')
parser.add_argument('input_file', type=str, help = '.csv file location of dataset')
map_args=parser.parse_args()

if map_args.objective == 'MAX':
    if map_args.eta != 0:
        sys.exit("set 'eta' = 0")
elif map_args.objective == 'MIN':
    if map_args.B != 0:
        sys.exit("set 'B' = 0")
else:
    sys.exit("Objective Functions must be 'MAX' or 'MIN'")


# store data into dataframe (pandas)
dataset = pd.read_csv(map_args.input_file)

# data item id dropped (not needed)
dataset = dataset.drop(['E',], axis=1)

num_clusters = len(dataset.C.unique())

# create clusters
C = []
for k in range(num_clusters):
    C.append(set())

# put data items into clusters
for index, row in dataset.iterrows():
    for k in range(num_clusters):
        if row['C'] == k + 1:
            C[k].add(index)
            break

# cluster column no longer needed
dataset = dataset.drop(['C'], axis=1)

# count data items in each cluster
for k in range(num_clusters):
    print("# of elements in cluster " + str(k+1) + ":", len(C[k]))

# get tags
tau = dataset.columns.values.tolist()
print("# of tags: ", len(tau))

# set B
Bud = map_args.B 
if map_args.B == 0:
    Bud = len(tau)

# create a matrix of data items and their tags
B = dataset.to_numpy()

print("-------------------------------------------------------------------------------------------------------------")
print("Starting ILP")
print("-------------------------------------------------------------------------------------------------------------")
ilp_starttime=datetime.now()
m=Model('test_ilp')

# Variables
n = len(B) # number of data items
N = len(tau) # number of tags
K = num_clusters # number of clusters

# y[j][k]: 1 if tag tau_j is in descriptor D_k, 0 otherwise
y = []
for j in range(N):
    tau = []
    for k in range(K):
        tau.append(m.addVar(vtype=GRB.BINARY, name="y_"+str(j)+","+str(k)))
    y.append(tau)

# z[i]: 1 if data item x_i is covered, 0 otherwise
z = []
for i in range(n):
    z.append(m.addVar(vtype=GRB.BINARY, name="z_"+str(i)))

# q[i]: number of tags in D_k that describe x_i (variable creation)
q = []
for i in range(n):
    q.append(m.addVar(vtype=GRB.INTEGER, name="q_"+str(i)))

# Constraints:
# q[i]: number of tags in D_k that describe x_i (variable initialization)
for i in range(n):
    cluster = 0
    for k in range(K):
        if i in C[k]:
            cluster = k
            break
    m.addConstr(quicksum(B[i][j] * y[j][cluster] for j in range(N)) == q[i])

# Ensures that at most B tags are used in total
if map_args.objective == "MAX":
    m.addConstr(quicksum(y[j][k] for j in range(N) for k in range(K)) <= Bud)

# a tag may appear in at most one descriptors
for j in range(N):
    m.addConstr(quicksum(y[j][k] for k in range(K)) <= 1)

# if q_i ≥ 1, we want to set z_i = 1; otherwise (i.e., q_i = 0), zi should be set to 0.
for i in range(n):
    m.addConstr(q[i] <= N*z[i])
for i in range(n):
    m.addConstr(N*z[i] <= q[i] + N - 1)

# solution set covers at least 'eta' objects
if map_args.objective == "MIN":
    m.addConstr(quicksum(z[i] for i in range(n)) >= int(map_args.eta))

# Objective:
# maximize total coverage
if map_args.objective == "MAX":
    print("Maximizing")
    m.setObjective(quicksum(z[i] for i in range(n)), GRB.MAXIMIZE)
# minimize total number of tags used
else:
    print("Minimizing")
    m.setObjective(quicksum(y[j][k] for j in range(N) for k in range(K)), GRB.MINIMIZE)

m.update()
m.write('ilp_icml.lp')

m.optimize()

# Solution Found
if m.status==GRB.Status.OPTIMAL:
    ilp_endtime=datetime.now()
    counts = []
    for k in range(K):
        count = 0
        for j in range(N):
            if y[j][k].X > 0:
                count += 1
                print(y[j][k].VarName)
        counts.append(count)
        print("Attributes selected from cluster " + str(k + 1) + ":", count)

    hit_counts = [0] * K
    for i in range(n):
        if z[i].X > 0:
            for k in range(K):
                if i in C[k]:
                    hit_counts[k] += 1
                    break

    print("# of tags picked = ", sum(counts))
    for k in range(K):
        print("# of elements hit in cluster " + str(k + 1) + ":", hit_counts[k])
    print("# of elements hit = ", sum(hit_counts))
else:
    print("No solution.")