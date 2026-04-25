"""Typed enumerations for SCPI parameter values.

All enum values match the exact SCPI strings accepted by the instrument,
so they can be passed directly to write() without conversion.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import numpy as np


class ChannelCoupling(str, Enum):
    AC = "AC"
    DC = "DC"
    GND = "GND"


class ChannelUnit(str, Enum):
    VOLT = "VOLT"
    AMPERE = "AMPere"


class ChannelBandwidth(str, Enum):
    FULL = "0"           # no limit
    BW_25MHZ = "25E6"
    BW_20MHZ = "20E6"


class AcquireType(str, Enum):
    NORMAL = "NORMal"
    AVERAGE = "AVERage"
    HRESOLUTION = "HRESolution"
    PEAK = "PEAK"


class TriggerSweep(str, Enum):
    AUTO = "AUTO"
    NORMAL = "NORMal"
    SINGLE = "SINGle"


class TriggerSlope(str, Enum):
    POSITIVE = "POSitive"
    NEGATIVE = "NEGative"
    EITHER = "EITHer"
    ALTERNATE = "ALTernate"


class TriggerSource(str, Enum):
    CH1 = "CHANnel1"
    CH2 = "CHANnel2"
    CH3 = "CHANnel3"
    CH4 = "CHANnel4"
    EXTERNAL = "EXTernal"
    LINE = "LINE"


class TriggerMode(str, Enum):
    EDGE = "EDGE"
    GLITCH = "GLITch"
    PATTERN = "PATTern"
    SHOLD = "SHOLd"
    TRANSITION = "TRANsition"
    TV = "TV"


class TimebaseMode(str, Enum):
    MAIN = "MAIN"
    WINDOW = "WINDow"
    XY = "XY"
    ROLL = "ROLL"


class WaveformFormat(str, Enum):
    BYTE = "BYTE"
    WORD = "WORD"
    ASCII = "ASCii"


class WaveformSource(str, Enum):
    CH1 = "CHANnel1"
    CH2 = "CHANnel2"
    CH3 = "CHANnel3"
    CH4 = "CHANnel4"
    FUNCTION = "FUNCtion"
    WMEMORY1 = "WMEMory1"
    WMEMORY2 = "WMEMory2"


class MeasureSource(str, Enum):
    CH1 = "CHANnel1"
    CH2 = "CHANnel2"
    CH3 = "CHANnel3"
    CH4 = "CHANnel4"
    FUNCTION = "FUNCtion"
    EXTERNAL = "EXTernal"


@dataclass
class WaveformPreamble:
    """Decoded :WAVeform:PREamble? response (10 comma-separated fields)."""
    format: int        # 0=BYTE, 1=WORD, 4=ASCii
    wf_type: int       # 0=NORMal, 1=PEAK, 2=AVERage, 3=HRESolution
    points: int
    count: int
    x_increment: float  # seconds per point
    x_origin: float     # time of first data point (seconds)
    x_reference: int    # index of reference point
    y_increment: float  # volts per unit
    y_origin: float     # voltage at centre screen
    y_reference: int    # data value at y_origin

    @classmethod
    def from_string(cls, raw: str) -> "WaveformPreamble":
        parts = [p.strip() for p in raw.split(",")]
        return cls(
            format=int(parts[0]),
            wf_type=int(parts[1]),
            points=int(parts[2]),
            count=int(parts[3]),
            x_increment=float(parts[4]),
            x_origin=float(parts[5]),
            x_reference=int(parts[6]),
            y_increment=float(parts[7]),
            y_origin=float(parts[8]),
            y_reference=int(parts[9]),
        )

    def to_volts(self, raw_data: np.ndarray) -> np.ndarray:
        return (raw_data.astype(float) - self.y_reference) * self.y_increment + self.y_origin

    def time_axis(self) -> np.ndarray:
        indices = np.arange(self.points)
        return (indices - self.x_reference) * self.x_increment + self.x_origin


@dataclass
class WaveformData:
    """A fully decoded, scaled waveform ready for analysis."""
    time: np.ndarray     # seconds
    voltage: np.ndarray  # volts
    preamble: WaveformPreamble
    source: str


@dataclass
class ChannelConfig:
    channel: int
    display: bool = True
    coupling: ChannelCoupling = ChannelCoupling.DC
    probe_attenuation: float = 1.0
    range_v: Optional[float] = None   # full-scale voltage range
    offset_v: float = 0.0
    invert: bool = False
    label: str = ""
    unit: ChannelUnit = ChannelUnit.VOLT
