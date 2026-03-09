import json
from datetime import datetime, timezone
from job.lib.s3 import S3Client
from job.core.metadata import PipelineCheckpoint

def get_checkpoint(s3_client: S3Client, bucket: str, key: str) -> PipelineCheckpoint | None:
    payload = s3_client.get_string(bucket=bucket, key=key)
    if not payload:
        return None

    checkpoint = json.loads(payload)
    event_id = checkpoint.get("last_event_id")    

    if event_id is None:
        return None
    
    return PipelineCheckpoint(
        last_event_id=event_id,
        record_count=checkpoint.get("record_count", 0),
        timstamp=datetime.fromisoformat(checkpoint.get("updated_at")),
    )


def commit_checkpoint(
        s3_client: S3Client,
        bucket: str,
        key: str,
        last_event_id: str,
        record_count: int
    ) -> None:

    checkpoint = {
        "last_event_id": last_event_id,
        "record_count": record_count,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    s3_client.upload_string(bucket=bucket, key=key, data=json.dumps(checkpoint))
