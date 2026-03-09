from dataclasses import dataclass
from datetime import datetime

@dataclass
class PipelineCheckpoint:
    last_event_id: str
    record_count: int
    timstamp: datetime