from typing import Optional

import boto3
from botocore.client import Config


class S3Client:
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> None:
        self._endpoint = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            session = boto3.session.Session()
            self._client = session.client(
                "s3",
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                config=Config(signature_version="s3v4"),
            )
        return self._client

    def get_bytes(self, bucket: str, key: str) -> bytes:
        client = self._get_client()
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
