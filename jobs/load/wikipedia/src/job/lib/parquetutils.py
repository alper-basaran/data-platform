from datetime import datetime
from io import BytesIO
from typing import Any

import pyarrow.parquet as pq


def build_partitioned_key(data_interval_ts: datetime) -> str:
    date_part = data_interval_ts.strftime("%Y-%m-%d")
    hour_part = data_interval_ts.strftime("%H")
    return f"/dt={date_part}/hh={hour_part}/page_events.parquet"


def read_parquet_rows(parquet_bytes: bytes) -> list[dict[str, Any]]:
    table = pq.read_table(BytesIO(parquet_bytes))
    return table.to_pylist()
