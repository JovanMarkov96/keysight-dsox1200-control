"""keysight_dsox1200 — Python driver for Keysight InfiniiVision 1200 X-Series oscilloscopes.

Supported models: DSOX1202A/G, DSOX1204A/G, EDUX1052A/G.

Quick start:
    from keysight_dsox1200 import DSOX1200, AcquireType, TriggerSource, TriggerSlope

    with DSOX1200("USB0::0x2A8D::0x1797::XXXXXXXX::0::INSTR") as scope:
        scope.reset()
        scope.configure_channel(1, coupling=ChannelCoupling.DC, scale_v=0.5)
        scope.configure_timebase(scale_s=1e-3)
        wf = scope.capture_waveform(1)
        print(f"Vpp = {scope.measure_vpp():.4f} V")
"""

from .instrument import DSOX1200
from .models import (
    AcquireType,
    ChannelCoupling,
    ChannelUnit,
    MeasureSource,
    TimebaseMode,
    TriggerSlope,
    TriggerSource,
    TriggerSweep,
    WaveformData,
    WaveformFormat,
    WaveformPreamble,
    WaveformSource,
    ChannelConfig,
)
from .errors import (
    DSO1200Error,
    ConnectionError,
    CommandError,
    TimeoutError,
    ValidationError,
)
from .discovery import list_instruments, auto_connect

__version__ = "0.1.0"
__all__ = [
    "DSOX1200",
    "AcquireType",
    "ChannelCoupling",
    "ChannelUnit",
    "MeasureSource",
    "TimebaseMode",
    "TriggerSlope",
    "TriggerSource",
    "TriggerSweep",
    "WaveformData",
    "WaveformFormat",
    "WaveformPreamble",
    "WaveformSource",
    "ChannelConfig",
    "DSO1200Error",
    "ConnectionError",
    "CommandError",
    "TimeoutError",
    "ValidationError",
    "list_instruments",
    "auto_connect",
]
