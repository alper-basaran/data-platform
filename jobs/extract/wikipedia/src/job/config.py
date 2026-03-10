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
    base_url: str = field(default=None, metadata={"required": True})
    interval_start: datetime = field(default=None, metadata={"required": True})
    interval_end: datetime = field(default=None, metadata={"required": True})
    api_page_size: int = field(default=100, metadata={"required": False})
    max_pages_per_interval: int = field(default=10, metadata={"required": False})
    api_rate_limit_per_second: int = field(default=5, metadata={"required": False})

    def __post_init__(self):
        self._validate()
        self._parse_numeric_fields()

    def _parse_numeric_fields(self):
        # TODO: This parsing needs to be metadata driven via type hints or explicit metadata

        try:
            self.api_page_size = int(self.api_page_size)
        except ValueError:
            raise InvalidJobConfigurationError(
                field_name="api_page_size",
                value=self.api_page_size,
                message="Invalid integer value",
            )

        try:
            self.max_pages_per_interval = int(self.max_pages_per_interval)
        except ValueError:
            raise InvalidJobConfigurationError(
                field_name="max_pages_per_interval",
                value=self.max_pages_per_interval,
                message="Invalid integer value",
            )

        try:
            self.api_rate_limit_per_second = int(self.api_rate_limit_per_second)
        except ValueError:
            raise InvalidJobConfigurationError(
                field_name="api_rate_limit_per_second",
                value=self.api_rate_limit_per_second,
                message="Invalid integer value",
            )

        try:
            if isinstance(self.interval_start, str):
                self.interval_start = datetime.fromisoformat(
                    self.interval_start.replace("Z", "+00:00")
                )
            if isinstance(self.interval_end, str):
                self.interval_end = datetime.fromisoformat(
                    self.interval_end.replace("Z", "+00:00")
                )
        except ValueError:
            raise InvalidJobConfigurationError(
                field_name="interval_start/interval_end",
                value=f"start={self.interval_start}, end={self.interval_end}",
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
            value = os.environ.get(env_var_name)
            config_dict[f.name] = value
        config = AppConfig(**config_dict)
        config._validate()
        return config
