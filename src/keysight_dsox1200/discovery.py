"""VISA resource discovery for Keysight InfiniiVision 1200 X-Series oscilloscopes.

Matches any instrument whose *IDN? string contains the model identifiers
for the 1200 X-Series family: DSOX1202, DSOX1204, EDUX1052.
"""

from __future__ import annotations
from typing import List, Tuple

try:
    import pyvisa
    _HAS_PYVISA = True
except ImportError:
    _HAS_PYVISA = False

_MODEL_SUBSTRINGS = ("DSO-X 120", "DSOX120", "EDUX1052", "DSO-X 1200")


def list_instruments(resource_manager=None) -> List[Tuple[str, str]]:
    """Return list of (visa_address, idn_string) for connected 1200 X-Series scopes.

    Args:
        resource_manager: existing pyvisa.ResourceManager, or None to create one.

    Returns:
        List of (address, idn) tuples. Empty if none found.

    Raises:
        ImportError: if pyvisa is not installed.
    """
    if not _HAS_PYVISA:
        raise ImportError("pyvisa is required for discovery. Install with: pip install pyvisa pyvisa-py")

    rm = resource_manager or pyvisa.ResourceManager()
    found: List[Tuple[str, str]] = []

    for addr in rm.list_resources():
        try:
            res = rm.open_resource(addr)
            res.timeout = 2000
            idn = res.query("*IDN?").strip()
            res.close()
            if any(sub in idn for sub in _MODEL_SUBSTRINGS):
                found.append((addr, idn))
        except Exception:
            pass

    return found


def auto_connect(resource_manager=None, prefer_usb: bool = True):
    """Open and return a pyvisa resource for the first 1200 X-Series scope found.

    Args:
        resource_manager: existing pyvisa.ResourceManager, or None to create one.
        prefer_usb: if True, sort USB resources before LAN ones.

    Returns:
        An open pyvisa resource (FormattedIO488 with *RST applied).

    Raises:
        RuntimeError: if no compatible scope is found.
        ImportError: if pyvisa is not installed.
    """
    instruments = list_instruments(resource_manager)
    if not instruments:
        raise RuntimeError("No Keysight InfiniiVision 1200 X-Series oscilloscope found.")

    if prefer_usb:
        instruments.sort(key=lambda x: (0 if x[0].startswith("USB") else 1))

    addr, idn = instruments[0]
    rm = resource_manager or pyvisa.ResourceManager()
    resource = rm.open_resource(addr)
    return resource
