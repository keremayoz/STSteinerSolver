# Copyright © Kerem Ayöz
# Reads the files consecutively and creates 2 arrays
# gene_names: (number of genes x 1) array that contains the names of genes
# gene_samples: (number of genes x number of features) array that contains only the feature values for genes
# After calculating the Pearson coefficient (by using numpy), it creates
# the network and wnetwork files

import numpy
import csv

# Names of files
file_names = ["aa.csv", "ap1.csv", "ap2.csv", "bp1.csv",
              "bp2.csv", "n1.csv", "n2.csv", "n3.csv"]

for files in file_names:
    # Index and dimension variable initializations
    i = 0
    width = 0
    height = 0

    # Calculating the file's data dimensions
    with open(files) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        # Determining dimensions of matrices
        for rowCount in readCSV:
            width += 1
            height = len(rowCount)

        print(files)
        print("Width: " + str(width - 1))
        print("Height: " + str(height - 1))
        print("  ")
