class DummyScorer():
    """
    Dummy scorer class, later this will score using the offline-trained GNN
    """
    def score(self, tx_id, subraph):
        return 0.5
