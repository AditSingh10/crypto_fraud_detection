from collections import namedtuple

StreamEvent = namedtuple("StreamEvent", ["time_step", "nodes", "edges"])


class StreamSimulator:
    """
    Returns a single event for each timestep of the format [timestep, nodes, edges]
    """
    def __init__(self, nodes_df, edges_df):
        self.nodes_df = nodes_df
        self.edges_df = edges_df
        self.timesteps = sorted(nodes_df["time_step"].unique())
        self.idx = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx >= len(self.timesteps):
            raise StopIteration
        t = self.timesteps[self.idx]
        self.idx += 1
        
        # Find node for current timestep
        nodes_t = self.nodes_df[self.nodes_df["time_step"] == t]
        nodes = []
        for _, row in nodes_t.iterrows():
            nodes.append(
                {
                    "txId": row["txId"],
                    "features": row.drop(["txId", "time_step"]).values.tolist(),
                    "time_step": t
                }
            )
        
        tx_ids = set(nodes_t["txId"])
        edges_t = self.edges_df[
            self.edges_df["txId1"].isin(tx_ids)
            & self.edges_df["txId2"].isin(tx_ids)
        ]
        edges = list(zip(edges_t["txId1"], edges_t["txId2"]))

        return StreamEvent(
            time_step=t,
            nodes=nodes,
            edges=edges,
        )

