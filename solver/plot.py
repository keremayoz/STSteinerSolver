import networkx as nx
import matplotlib.pyplot as plt
import pandas as pandas
import csv


data = pandas.read_csv("n3_05.txt")
G = nx.Graph()
'''
nodes = set()


for i in range(len(data)):
    nodes.add(data.iloc[i][0].split("\t")[1])
    nodes.add(data.iloc[i][0].split("\t")[0])

nodes = list(nodes)

for i in range(len(nodes)):
    G.add_node(nodes[i])
'''
for i in range(len(data)):
    G.add_edge(data.iloc[i][0].split("\t")[1], data.iloc[i][0].split("\t")[0])



plt.figure(figsize=(30,30))


graph_pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, graph_pos, node_size=10, node_color='blue', alpha=0.5)
nx.draw_networkx_edges(G, graph_pos, edge_size=6)
nx.draw_networkx_labels(G, graph_pos, font_size=6, font_family='sans-serif')
plt.savefig("plot.png", dpi=1000)

plt.savefig("plot.pdf")
plt.show()

