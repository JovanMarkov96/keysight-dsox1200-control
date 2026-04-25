"""Exception hierarchy for keysight_dsox1200."""


class DSO1200Error(Exception):
    """Base exception for all driver errors."""


class ConnectionError(DSO1200Error):
    """Failed to open or maintain a VISA connection."""


class CommandError(DSO1200Error):
    """Instrument returned a SCPI error (from :SYSTem:ERRor?)."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"SCPI error {code}: {message}")


class TimeoutError(DSO1200Error):
    """Operation exceeded the configured timeout."""


class ValidationError(DSO1200Error):
    """Invalid argument passed to a driver method."""
