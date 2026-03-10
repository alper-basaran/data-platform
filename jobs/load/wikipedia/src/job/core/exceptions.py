class InvalidJobConfigurationError(Exception):
    def __init__(self, field_name: str, value: str, message: str):
        super().__init__(
            f"Invalid configuration for '{field_name}': {value}. {message}"
        )
