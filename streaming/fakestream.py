class FakeStream:
    def __init__(self):
        self.events = [
            type("Event", (), {
                "nodes": [
                    {"txId": "A", "features": [1, 2], "timestep": 1}
                ],
                "edges": []
            })()
        ]
        self.idx = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.idx >= len(self.events):
            raise StopIteration
        event = self.events[self.idx]
        self.idx += 1
        return event