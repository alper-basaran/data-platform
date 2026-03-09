import json
from typing import Any

from psycopg import connect

# TODO: Parameterize table name and schema

class PostgresClient:
    def __init__(self, host: str, port: int, dbname: str, user: str, password: str) -> None:
        self._conninfo = (
            f"host={host} "
            f"port={port} "
            f"dbname={dbname} "
            f"user={user} "
            f"password={password}"
        )

    # TODO: hard-coded table names and upsert logic - this is specific to the wikipedia_page_changes table and should be refactored
    def persist_page_changes(self, rows: list[dict[str, Any]], source_object_key: str) -> int:
        payload = []

        for row in rows:
            change_id = row.get("change_id")
            if change_id is None:
                continue

            payload.append(
                (
                    int(change_id),
                    row.get("revision_id_old"),
                    row.get("revision_id_new"),
                    row.get("title"),
                    row.get("timestamp"),
                    row.get("user"),
                    row.get("comment"),
                    row.get("old_length"),
                    row.get("new_length"),
                    json.dumps(row.get("tags") or []),
                    row.get("log_type"),
                    row.get("log_action"),
                    row.get("raw_json"),
                    source_object_key,
                )
            )

        if not payload:
            return 0

        with connect(self._conninfo) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO wikipedia_page_changes (
                        change_id,
                        revision_id_old,
                        revision_id_new,
                        title,
                        event_timestamp,
                        username,
                        comment,
                        old_length,
                        new_length,
                        tags,
                        log_type,
                        log_action,
                        raw_json,
                        source_object_key
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s::jsonb, %s, %s, %s::jsonb, %s
                    )
                    ON CONFLICT (change_id) DO UPDATE SET
                        revision_id_old = EXCLUDED.revision_id_old,
                        revision_id_new = EXCLUDED.revision_id_new,
                        title = EXCLUDED.title,
                        event_timestamp = EXCLUDED.event_timestamp,
                        username = EXCLUDED.username,
                        comment = EXCLUDED.comment,
                        old_length = EXCLUDED.old_length,
                        new_length = EXCLUDED.new_length,
                        tags = EXCLUDED.tags,
                        log_type = EXCLUDED.log_type,
                        log_action = EXCLUDED.log_action,
                        raw_json = EXCLUDED.raw_json,
                        source_object_key = EXCLUDED.source_object_key,
                        loaded_at = NOW()
                    """,
                    payload,
                )
            conn.commit()

        return len(payload)
