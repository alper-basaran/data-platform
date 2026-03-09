import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from typing import Optional


class S3Client:
    #TODO: docstring
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

    def upload_string(self, bucket: str, key: str, data: str) -> None:
        """Upload a text payload to the given bucket/key."""
        client = self._get_client()
        client.put_object(Bucket=bucket, Key=key, Body=data)

    def upload_bytes(self, bucket: str, key: str, data: bytes) -> None:
        """Upload a bytes payload to the given bucket/key."""
        client = self._get_client()
        client.put_object(Bucket=bucket, Key=key, Body=data)

    def get_string(self, bucket: str, key: str) -> Optional[str]:
        """Get object body as UTF-8 text, returning None if object does not exist."""
        client = self._get_client()
        try:
            response = client.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read()
            return body.decode("utf-8")
        
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("NoSuchKey", "404"):
                return None
            raise