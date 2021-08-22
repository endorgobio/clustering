import numpy as np
import pandas as pd

class Node:
    def __init__(self, id, lat=0, long=0, demand=0):
        self.id = id
        self.lat = lat
        self.long = long
        self.demand = demand


class Cluster:
    def __init__(self, center):
        self.center = center
        self.node_list = []
        self.node_list.append(center)
        self.distAllToAll = []
        self.distAllToCent = []
        self.load = 0

    def get_measures(self, distances):
        # Distances all to center
        for node_id in self.node_list:
            self.distAllToCent.append(distances[(self.center.id, node_id.id)])

        # Distances all pair of nodes
        # It assumes non symmetric distances but also work for symmetric
        for node1 in self.node_list:
            for node2 in self.node_list:
                self.distAllToAll.append(distances[(node1.id, node2.id)])

        # get cluster load
        self.load = np.sum([node.demand for node in self.node_list])


class Solution:
    def __init__(self, nClusters, df):
        self.nClusters = nClusters
        self.clusters_list = []
        self.objectiveValue = 0
        self.dfPrint = df


    def get_objvalue(self, obj_function):
        def sum_alltocenter():
            union = []
            for cluster in self.clusters_list:
                union += cluster.distAllToCent
            s = np.sum(union)
            # s = np.sum([cluster.distAllToCent for cluster in self.clusters_list])
            return s

        def sum_alltoall():
            union = []
            for cluster in self.clusters_list:
                union += cluster.distAllToAll
            s = np.sum(union)
            # s = np.sum([cluster.distAllToAll for cluster in self.clusters_list])
            return s

        def load_range():
            load_max = self.load = np.max([cluster.load for cluster in self.clusters_list])
            load_min = self.load = np.min([cluster.load for cluster in self.clusters_list])
            return load_max - load_min

        # Dictionary that compiles options for the objective function
        functions = {
            'sumAllToCenter': sum_alltocenter,
            'sumAllToAll': sum_alltoall,
            'loadRange': load_range
        }

        # computes the objective with the given objective function
        obj = functions[obj_function]()
        return obj

    def get_dfToPrint(self):
        self.dfPrint['zona_id'] = -99
        self.dfPrint['zona'] = None
        for i in range(len(self.clusters_list)):
            for node in self.clusters_list[i].node_list:
                self.dfPrint.loc[self.dfPrint['id'] == node.id, 'zona_id'] = i + 1
                self.dfPrint.loc[self.dfPrint['id'] == node.id, 'zona'] = "zona" + str(i + 1)


class Instance:
    def __init__(self, df, nodes, n_clusters, epsilon):
        self.df = df
        self.nodes = nodes
        self.n_clusters = n_clusters
        self.epsilon = epsilon

