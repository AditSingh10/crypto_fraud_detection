from collections import defaultdict, deque

class GraphBuffer():

    def __init__(self):
        self.nodes = {} # txId - > features
        self.adj_list = defaultdict(set) # txId - > neighbors

    def add_nodes(self, nodes):
        for node in nodes:
            self.nodes[node["txId"]] = node
    
    def add_edges(self, edges):
        for src, dest in edges:
            self.adj_list[src].add(dest)
            self.adj_list[dest].add(src)

    def get_subgraph(self, center_tx_id, k_hops=2, max_nodes=100):
        visited = set([center_tx_id])
        queue = deque([(center_tx_id, 0)])

        while queue:
            current, depth = queue.popleft()

            if depth == k_hops:
                continue

            for neighbor in self.adj_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                if len(visited) >= max_nodes:
                    break
                queue.append((neighbor, depth + 1))
        sub_nodes = [self.nodes[tx_id] for tx_id in visited]

        sub_edges = []
        for tx_id in visited:
            for dest in self.adj_list[tx_id]:
                if dest in visited:
                    sub_edges.append((tx_id, dest))
        
        return {
            "nodes" : sub_nodes,
            "edges" : sub_edges,
            "center" : center_tx_id
        }
