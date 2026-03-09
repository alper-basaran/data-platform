from datetime import datetime
from io import BytesIO
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

def convert_to_parquet_bytes(
        events: list[dict[str, Any]],
        mapper_fn: callable,
        compression: str = "snappy"
    ) -> bytes:
    
    rows: list[dict[str, Any]] = []

    for event in events:        
        rows.append(
            mapper_fn(event)
        )          

    table = pa.Table.from_pylist(rows)
    buffer = BytesIO()
    pq.write_table(table, buffer, compression=compression)

    return buffer.getvalue()


def build_partitioned_key(
        data_interval_ts: datetime,
    ) -> str:
    
    date_part = data_interval_ts.strftime("%Y-%m-%d")
    hour_part = data_interval_ts.strftime("%H")
    
    return (
        f"/dt={date_part}/hh={hour_part}/"
        f"page_events.parquet"
    )