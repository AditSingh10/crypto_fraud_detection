from streaming.graph_buffer import GraphBuffer

gb = GraphBuffer()

t1_nodes = [
    {"txId": "A", "features": [1.0, 0.5], "timestep": 1},
    {"txId": "B", "features": [0.3, 0.8], "timestep": 1},
]

t1_edges = [
    ("A", "B")
]

gb.add_nodes(t1_nodes)
gb.add_edges(t1_edges)

print(gb.nodes.keys())
print(dict(gb.adj_list))