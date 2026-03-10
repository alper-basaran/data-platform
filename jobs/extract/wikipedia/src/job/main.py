#!/usr/bin/env python3
import sys

from requests_ratelimiter import LimiterSession

from job.config import AppConfig
from job.lib.logger import configure_logging, get_logger
from job.lib.parquetutils import build_partitioned_key, convert_to_parquet_bytes
from job.lib.s3 import S3Client
from job.lib.wikipedia import WikipediaClient

CHECKPOINT_KEY = "wikipedia/_state/extract_checkpoint.json"

configure_logging()
logger = get_logger(__package__)


def run(config: AppConfig):
    logger.info("Wikipedia Extract Service Starting...")

    s3_client = S3Client(
        endpoint_url=config.s3_endpoint_url,
        access_key=config.s3_access_key,
        secret_key=config.s3_secret_key,
    )

    api_client = WikipediaClient(
        base_url=config.base_url,
        session=LimiterSession(per_second=config.api_rate_limit_per_second),
    )

    all_changes = api_client.get_changes_for_interval(
        interval_start=config.interval_start,
        interval_end=config.interval_end,
        page_limit=config.api_page_size,
        max_pages=config.max_pages_per_interval,
        type=["new", "edit"],
    )

    if not all_changes:
        logger.info("No new changes found. Exiting without writes.")
        return

    partition_key = build_partitioned_key(
        data_interval_ts=config.interval_start,
    ).lstrip("/")
    output_key = f"{config.raw_folder.rstrip('/')}/{partition_key}"

    parquet_bytes = convert_to_parquet_bytes(
        all_changes, mapper_fn=lambda e: e.model_dump()
    )
    s3_client.upload_bytes(bucket=config.s3_bucket, key=output_key, data=parquet_bytes)

    logger.info(
        f"Persisted {len(all_changes)} events to s3://{config.s3_bucket}/{output_key}."
    )


def main():
    try:
        configure_logging()
        config = AppConfig.from_env()

        run(config)
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
