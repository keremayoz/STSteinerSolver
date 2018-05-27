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

        # Creating gene_name and gene_samples arrays
        gene_samples = [[0 for x in range(width - 1)]
                        for y in range(height - 1)]
        gene_name = [[0 for x in range(1)] for y in range(height - 1)]

    # Reading the data
    with open(files) as csvfile2:
        readCSV2 = csv.reader(csvfile2, delimiter=',')
        for row in readCSV2:
            s = 0
            for s in range(0, height - 1):
                if i == 0:
                    gene_name[s] = row[s + 1]
                elif i != 0:
                    gene_samples[s][i - 1] = float(row[s + 1])
            i += 1

    #.network files
    c_06 = open((files[:-4] + "_06.network"), 'w')
    c_07 = open((files[:-4] + "_07.network"), 'w')
    c_08 = open((files[:-4] + "_08.network"), 'w')

    #.wnetwork files
    wc_06 = open((files[:-4] + "_06.wnetwork"), 'w')
    wc_07 = open((files[:-4] + "_07.wnetwork"), 'w')
    wc_08 = open((files[:-4] + "_08.wnetwork"), 'w')

    # Calculate Pearson correlation of each gene pair and write them into the
    # appropriate file
    for j in range(0, height - 1):
        for k in range(0, height - 1):
            if j != k:
                correlation = numpy.abs(numpy.corrcoef(gene_samples[j], gene_samples[k])[0, 1])
                if correlation >= 0.8:
                    c_08.write(gene_name[j] + "\t" + gene_name[k] + "\n")
                    wc_08.write(gene_name[j] + "\t" + gene_name[k] + "\t" + str(correlation) + "\n")
                if correlation >= 0.7:
                    c_07.write(gene_name[j] + "\t" + gene_name[k] + "\n")
                    wc_07.write(gene_name[j] + "\t" + gene_name[k] + "\t" + str(correlation) + "\n")
                if correlation >= 0.6:
                    c_06.write(gene_name[j] + "\t" + gene_name[k] + "\n")
                    wc_06.write(gene_name[j] + "\t" + gene_name[k] + "\t" + str(correlation) + "\n")

    c_06.close()
    c_07.close()
    c_08.close()
    wc_06.close()
    wc_07.close()
    wc_08.close()
