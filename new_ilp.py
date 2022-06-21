from gurobipy import *
import argparse
from datetime import datetime
import random as rand
import pandas as pd
import numpy as np
import sys

# read input args
# new_ilp.py alpha eta clusters input_file
parser=argparse.ArgumentParser()
parser.add_argument('alpha', type=int)
parser.add_argument('eta', type=int)
parser.add_argument('clusters', type=int, help="Input number of clusters")
parser.add_argument('input_file', type=str, help="Input file path")
map_args=parser.parse_args()

# store data into dataframe (pandas)
dataset = pd.read_csv(map_args.input_file)

# data item id dropped (not needed)
dataset = dataset.drop(['E',], axis=1)

# create clusters
C = []
for k in range(map_args.clusters):
    C.append([])

# put data items into clusters
for index, row in dataset.iterrows():
    for k in range(map_args.clusters):
        if row['C'] == k + 1:
            C[k].append(index)
            break

# cluster column no longer needed
dataset = dataset.drop(['C'], axis=1)

# count data items in each cluster
for k in range(map_args.clusters):
    print("# of elements in cluster" + str(k+1) + ":", len(C[k]))

# get tags
tau = dataset.columns.values.tolist()
print("# of tags: ", len(tau))

# create a matrix of data items and their tags
B = dataset.to_numpy()

print("-------------------------------------------------------------------------------------------------------------")
print("Starting ILP")
print("-------------------------------------------------------------------------------------------------------------")
ilp_starttime=datetime.now()
m=Model('test_ilp')

# Variables
y=[]
z=[]
n = len(B) # number of data items
N = len(tau) # number of tags
K = map_args.clusters # number of clusters

# y[j][k]: 1 if tag tau_j is in descriptor D_k, 0 otherwise
for j in range(N):
    tau = []
    for k in range(K):
        tau.append(m.addVar(vtype=GRB.BINARY, name="y_"+str(j)+","+str(k)))
    y.append(tau)

# z[i]: 1 if data item x_i is covered
for i in range(n):
    z.append(m.addVar(vtype=GRB.BINARY, name="z_"+str(i)))

# Constraints:
# size of each descriptor must be at most 'alpha'
for k in range(K):
    m.addConstr(quicksum(y[j][k] for j in range(N)) <= int(map_args.alpha))

# TO_DO
for k in range(K):
    for i in range(len(C[k])):
        m.addConstr(quicksum(B[i][j] * y[j][k] for j in range(N)) >= z[i])

# a tag may appear in at most one descriptors
for j in range(N):
    m.addConstr(quicksum(y[j][k] for j in range(K)) <= 1)

# solution set covers at least 'eta' objects
m.addConstr(quicksum(z[i] for i in range(n)) >= int(map_args.eta))

# Objective:
# maximize total coverage
m.setObjective(quicksum(z[i] for i in range(n)), GRB.MAXIMIZE)

# minimize total number of tags used
## m.setObjective(quicksum(y[j][k] for j in range(N) for k in range(K)), GRB.MINIMIZE)

m.update()
m.write('ilp_icml.lp')

m.optimize()

# 
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
