from streaming.graph_buffer import GraphBuffer
from streaming.fakestream import FakeStream
from streaming.dummy_scorer import DummyScorer
from streaming.streaming_service import StreamingService

service = StreamingService(
    stream=FakeStream(),
    graph_buffer=GraphBuffer(),
    scorer=DummyScorer()
)

print(service.process_next_event())