import pandas as pd
import os

from streaming.graph_buffer import GraphBuffer
from streaming.fakestream import FakeStream
from streaming.dummy_scorer import DummyScorer
from streaming.streaming_service import StreamingService
from streaming.stream_simulator import StreamSimulator


DATA_DIR = os.environ["ELLIPTIC_DATA_DIR"]

nodes_df = pd.read_csv(f"{DATA_DIR}/elliptic_bitcoin_dataset/elliptic_txs_features.csv", header=None)
edges_df = pd.read_csv(f"{DATA_DIR}/elliptic_bitcoin_dataset/elliptic_txs_edgelist.csv")

nodes_df = nodes_df.rename(columns={0: "txId", 1: "time_step"})

service = StreamingService(
    stream=StreamSimulator(nodes_df, edges_df),
    graph_buffer=GraphBuffer(),
    scorer=DummyScorer()
)

# print(service.process_next_event())

for i in range(1, 4):
    results = service.process_next_event()
    print(f"Processed {len(results)} transactions in timestep {i}")

