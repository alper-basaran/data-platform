import sys

from job.config import AppConfig
from job.lib.logger import configure_logging, get_logger
from job.lib.parquetutils import build_partitioned_key, read_parquet_rows
from job.lib.postgres import WikipediaPageChangesWriter
from job.lib.s3 import S3Client
from job.lib.warehouse import PostgresWarehouseWriter

configure_logging()
_logger = get_logger(__package__)
JOB_NAME = "wikipedia_load_job"


def run(config: AppConfig):
    _logger.info(f"Starting job {JOB_NAME}")

    s3_client = S3Client(
        endpoint_url=config.s3_endpoint_url,
        access_key=config.s3_access_key,
        secret_key=config.s3_secret_key,
    )

    partition_key = build_partitioned_key(config.interval_start).lstrip("/")
    source_object_key = f"{config.raw_folder.rstrip('/')}/{partition_key}"

    _logger.info(f"Fetching parquet object s3://{config.s3_bucket}/{source_object_key}")
    parquet_bytes = s3_client.get_bytes(bucket=config.s3_bucket, key=source_object_key)

    rows = read_parquet_rows(parquet_bytes)
    if not rows:
        _logger.info("No rows found in parquet file. Exiting without writes.")
        return

    warehouse_writer = PostgresWarehouseWriter(
        host=config.pg_host,
        port=config.pg_port,
        dbname=config.pg_db,
        user=config.pg_user,
        password=config.pg_password,
    )
    page_changes_writer = WikipediaPageChangesWriter(warehouse_client=warehouse_writer)

    loaded_count = page_changes_writer.persist_page_changes(
        table="wikipedia_page_changes", rows=rows, source_object_key=source_object_key
    )

    _logger.info(
        f"Loaded {loaded_count} rows into Postgres table wikipedia_page_changes from {source_object_key}."
    )
    _logger.info(f"Job {JOB_NAME} completed successfully.")


def main():
    try:
        configure_logging()
        config = AppConfig.from_env()

        run(config)
        sys.exit(0)
    except Exception as exc:
        _logger.error(f"Error occurred: {str(exc)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
