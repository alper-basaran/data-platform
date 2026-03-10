from unittest.mock import create_autospec

from job.lib.sink import WikipediaPageChangesWriter
from job.lib.warehouse import WarehouseWriter


def test_persist_page_changes_maps_fields_and_filters_missing_change_id():

    # Arrange
    warehouse_writer = create_autospec(WarehouseWriter, instance=True, spec_set=True)
    warehouse_writer.upsert.return_value = 1
    writer = WikipediaPageChangesWriter(warehouse_client=warehouse_writer)

    rows = [
        {
            "change_id": "123",
            "revision_id_old": 10,
            "revision_id_new": 11,
            "title": "Python",
            "timestamp": "2026-03-10T10:00:00Z",
            "user": "alice",
            "comment": "typo fix",
            "old_length": 100,
            "new_length": 110,
            "log_type": "edit",
            "log_action": "update",
        },
        {
            "change_id": None,
            "title": "Should be ignored",
        },
    ]

    # Act
    result = writer.persist_page_changes(
        table="wikipedia_page_changes",
        rows=rows,
        source_object_key="wikipedia/events/day=2026-03-10/hour=10/file.parquet",
    )

    # Assert
    assert result == 1
    warehouse_writer.upsert.assert_called_once_with(
        table="wikipedia_page_changes",
        rows=[
            {
                "change_id": 123,
                "revision_id_old": 10,
                "revision_id_new": 11,
                "title": "Python",
                "event_timestamp": "2026-03-10T10:00:00Z",
                "username": "alice",
                "comment": "typo fix",
                "old_length": 100,
                "new_length": 110,
                "log_type": "edit",
                "log_action": "update",
                "source_object_key": "wikipedia/events/day=2026-03-10/hour=10/file.parquet",
            }
        ],
        unique_key=["change_id"],
    )
