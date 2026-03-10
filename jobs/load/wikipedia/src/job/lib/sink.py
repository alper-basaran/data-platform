from typing import Any

from job.lib.warehouse import WarehouseWriter

# TODO: Parameterize table name and schema
# TODO: Add table partitioning (day+hour on event_timestamp) once schema management is centralized.


class WikipediaPageChangesWriter:
    def __init__(self, warehouse_client: WarehouseWriter) -> None:
        self._warehouse_client = warehouse_client

    def persist_page_changes(
        self, table: str, rows: list[dict[str, Any]], source_object_key: str
    ) -> int:
        payload_rows: list[dict[str, Any]] = []

        for row in rows:
            change_id = row.get("change_id")
            if change_id is None:
                continue

            payload_rows.append(
                {
                    "change_id": int(change_id),
                    "revision_id_old": row.get("revision_id_old"),
                    "revision_id_new": row.get("revision_id_new"),
                    "title": row.get("title"),
                    "event_timestamp": row.get("timestamp"),
                    "username": row.get("user"),
                    "comment": row.get("comment"),
                    "old_length": row.get("old_length"),
                    "new_length": row.get("new_length"),
                    "log_type": row.get("log_type"),
                    "log_action": row.get("log_action"),
                    "source_object_key": source_object_key,
                }
            )

        return self._warehouse_client.upsert(
            table=table,
            rows=payload_rows,
            unique_key=["change_id"],
        )
