# Copyright © Kerem Ayöz
# Reads the files consecutively and creates 2 arrays
# gene_names: (number of genes x 1) array that contains the names of genes
# gene_samples: (number of genes x number of features) array that contains only the feature values for genes
# After calculating the Pearson coefficient (by using numpy), it creates
# the network and wnetwork files

import numpy
import csv

# Names of files
file_names = ["ap1.csv", "ap2.csv", "bp1.csv",
              "bp2.csv", "n1.csv", "n2.csv", "n3.csv"]

for files in file_names:

    #.network files to read data
    c_06 = files[:-4] + "_06.network"
    c_07 = files[:-4] + "_07.network"
    c_08 = files[:-4] + "_08.network"

    networkFiles = [c_06, c_07, c_08]

    for eachFile in networkFiles:
        nodes = []
        edgeCount = 0
        # Reading the data
        with open(eachFile) as nf:
            readNetwork = csv.reader(nf, delimiter=',')
            for row in readNetwork:
                edgeCount += 1
                size = -1
                for i in range(len(row[0])):
                    if row[0][i] == "\t":
                        size = i
                        break
                geneName = row[0][0:size]
                nodes.append(geneName)

        uniqueNodeCount = len(list(set(nodes)))
        print(eachFile)
        print("Number of nodes: " + str(uniqueNodeCount))
        print("Number of edges: " + str(edgeCount))
