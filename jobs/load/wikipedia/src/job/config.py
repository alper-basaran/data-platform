import os
from dataclasses import dataclass, field, fields
from datetime import datetime

from job.core.exceptions import InvalidJobConfigurationError

ENV_PREFIX = "APPCONF__"


@dataclass
class AppConfig:
    s3_endpoint_url: str = field(default=None, metadata={"required": True})
    s3_access_key: str = field(default=None, metadata={"required": True})
    s3_secret_key: str = field(default=None, metadata={"required": True})
    s3_bucket: str = field(default=None, metadata={"required": True})
    raw_folder: str = field(default=None, metadata={"required": True})
    interval_start: datetime = field(default=None, metadata={"required": True})
    pg_host: str = field(default=None, metadata={"required": True})
    pg_port: int = field(default=5432, metadata={"required": False})
    pg_db: str = field(default="wikipedia", metadata={"required": False})
    pg_user: str = field(default=None, metadata={"required": True})
    pg_password: str = field(default=None, metadata={"required": True})

    def __post_init__(self):
        self._validate()
        self._parse_fields()

    def _parse_fields(self):
        try:
            self.pg_port = int(self.pg_port)
        except ValueError:
            raise InvalidJobConfigurationError(
                field_name="pg_port",
                value=self.pg_port,
                message="Invalid integer value",
            )

        try:
            if isinstance(self.interval_start, str):
                self.interval_start = datetime.fromisoformat(
                    self.interval_start.replace("Z", "+00:00")
                )
        except ValueError:
            raise InvalidJobConfigurationError(
                field_name="interval_start",
                value=str(self.interval_start),
                message="Invalid datetime format, expected ISO 8601",
            )

    def _validate(self):
        missing = []
        for f in fields(self):
            if f.metadata.get("required", False) and getattr(self, f.name) in (
                None,
                "",
            ):
                missing.append(f.name)

        if missing:
            raise InvalidJobConfigurationError(
                field_name=", ".join(missing),
                value="",
                message="Missing required config fields",
            )

    @staticmethod
    def from_env() -> "AppConfig":
        config_dict = {}
        for f in fields(AppConfig):
            env_var_name = f"{ENV_PREFIX}{f.name.upper()}"
            config_dict[f.name] = os.environ.get(env_var_name)

        config = AppConfig(**config_dict)
        config._validate()
        return config
