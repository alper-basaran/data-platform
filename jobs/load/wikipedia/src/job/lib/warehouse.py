from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from psycopg import connect


class WarehouseWriter(ABC):
    @abstractmethod
    def __init__(
        self,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str) -> None: ...        

    @abstractmethod
    def upsert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        unique_key: list[str],
    ) -> int: ...        


class PostgresWarehouseWriter(WarehouseWriter): 
    def __init__(self, host: str, port: int, dbname: str, user: str, password: str) -> None:
        self._conninfo = (
            f"host={host} "
            f"port={port} "
            f"dbname={dbname} "
            f"user={user} "
            f"password={password}"
        )

    def _execute_many(self, statement: str, payload: Sequence[tuple[Any, ...]]) -> int:
        if not payload:
            return 0

        with connect(self._conninfo) as conn:
            with conn.cursor() as cur:
                cur.executemany(statement, payload)
            conn.commit()

        return len(payload)

    @staticmethod
    def _quote_ident(identifier: str) -> str:
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    def upsert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        unique_key: list[str],
    ) -> int:
        if not rows:
            return 0

        if not unique_key:
            raise ValueError("unique_key must contain at least one column")

        columns = list(rows[0].keys())
        update_columns = [column for column in columns if column not in set(unique_key)]

        quoted_columns = ", ".join(self._quote_ident(column) for column in columns)
        value_placeholders = ", ".join("%s" for _ in columns)
        conflict_target = ", ".join(self._quote_ident(key) for key in unique_key)
        update_clause = ",\n                        ".join(
            f"{self._quote_ident(column)} = EXCLUDED.{self._quote_ident(column)}"
            for column in update_columns
        )

        upsert_sql = f"""
                    INSERT INTO {self._quote_ident(table)} (
                        {quoted_columns}
                    ) VALUES (
                        {value_placeholders}
                    )
                    ON CONFLICT ({conflict_target}) DO UPDATE SET
                        {update_clause}
                    """

        payload: list[tuple[Any, ...]] = []

        for row in rows:
            payload.append(tuple(row.get(column) for column in columns))

        return self._execute_many(statement=upsert_sql, payload=payload)
