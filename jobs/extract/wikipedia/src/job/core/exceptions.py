
class InvalidJobConfigurationError(Exception):
    """Custom exception raised when the job configuration is invalid."""
    def __init__(self, field_name: str, value: str, message: str):
        super().__init__(f"Invalid configuration for '{field_name}': {value}. {message}")
        