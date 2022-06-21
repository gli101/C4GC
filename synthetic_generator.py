# create csv file for synthetic data
# used for experiments in (PAPER NAME PLACEHOLDER)

import csv
import argparse
import random

parser=argparse.ArgumentParser()
parser.add_argument('num_o_objs', type=int)
parser.add_argument('num_o_tags', type=int)
parser.add_argument('clusters', type=int)
parser.add_argument('tag_prob', type=float)
map_args = parser.parse_args()

# create header data
header = []
header.append('E')
for i in range(map_args.num_o_tags):
    header.append('A' + str(i))
header.append('C')

# generate data for each object
data = []
cluster_ct = [0] * map_args.clusters
for i in range(map_args.num_o_objs):
    row = []
    row.append(str(i))

    # randomly assign tag j to object i with probability 'tag_prob'
    for j in range(map_args.num_o_tags):
        tag = random.random()
        if tag <= map_args.tag_prob:
            row.append(1)
        else:
            row.append(0)
    
    # randomly select a cluster for object
    cluster = random.random()
    for j in range(1, map_args.clusters+1):
        if cluster < j/map_args.clusters:
            row.append(j)
            cluster_ct[j-1] += 1
            break
    data.append(row)

# print object counts for each cluster
for i in range (map_args.clusters):
    print('Objects in cluster ' + str(i+1) + ':', cluster_ct[i])

# naming convention 'synthetic_data_(number of objects)_(number of tags)_(number of clusters)_(tag probability).csv'
file_name = 'synthetic_data_' + str(map_args.num_o_objs) + '_' + str(map_args.num_o_tags) + '_' + str(map_args.clusters) + '_' + str(map_args.tag_prob) + '.csv'

# write to csv file
with open(file_name, 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data)