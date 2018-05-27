import pandas as pandas
import csv
import re
import fileinput
import sys


# Taken from @Jason
# https://stackoverflow.com/questions/39086/search-and-replace-a-line-in-a-file-in-python?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
def replaceAll(file, searchExp, replaceExp):
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp, replaceExp)
        sys.stdout.write(line)


# Names of files
file_names = ["ap1_06.network", "ap2_06.network", "bp1_06.network", "bp2_06.network", "n1_06.network", "n2_06.network", "n3_06.network",
              "ap1_07.network", "ap2_07.network", "bp1_07.network", "bp2_07.network", "n1_07.network", "n2_07.network", "n3_07.network", "ap1_08.network", "ap2_08.network", "bp1_08.network", "bp2_08.network", "n1_08.network", "n2_08.network", "n3_08.network", "ap1_06.wnetwork", "ap2_06.wnetwork", "bp1_06.wnetwork", "bp2_06.wnetwork", "n1_06.wnetwork", "n2_06.wnetwork", "n3_06.wnetwork",
              "ap1_07.wnetwork", "ap2_07.wnetwork", "bp1_07.wnetwork", "bp2_07.wnetwork", "n1_07.wnetwork", "n2_07.wnetwork", "n3_07.wnetwork", "ap1_08.wnetwork", "ap2_08.wnetwork", "bp1_08.wnetwork", "bp2_08.wnetwork", "n1_08.wnetwork", "n2_08.wnetwork", "n3_08.wnetwork"]


# Read the tsv file as an array ?
data = pandas.read_csv("scRNA_bspan_name_map.tsv")

# Read the file
for everyFile in file_names:
    oldData = pandas.read_csv(everyFile)
    for i in range(len(data)):
        old = data.iloc[i][0].split("\t")[0]
        new = data.iloc[i][0].split("\t")[1]
        replaceAll(everyFile, old, new)
    print(everyFile + " is completed.")
