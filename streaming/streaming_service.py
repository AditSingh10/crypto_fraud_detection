class StreamingService:
    """
    This service consumes a stream of transaction events, updates a graph buffer, and 
    scores the new transactions using trained GNN.
    """

    def __init__(self, stream, graph_buffer, scorer):
        self.stream = stream
        self.graph_buffer = graph_buffer
        self.scorer = scorer
    
    def process_next_event(self):
        # Get next event from stream
        event = next(self.stream)
        # Add nodes and edges to graph buffer
        self.graph_buffer.add_nodes(event.nodes)
        self.graph_buffer.add_edges(event.edges)

        results = []
        for node in event.nodes:
            tx_id = node["txId"]

            # extract local neighborhood for inference
            subgraph = self.graph_buffer.get_subgraph(tx_id)

            # Score risk
            risk_score = self.scorer.score(tx_id, subgraph)

            results.append(
                {
                    "txId": tx_id,
                    "risk_score": risk_score
                }
            )

        return results


        pass
    
    

