"""Tests for SCPI command string formatting and enum-to-string conversion.

All tests are offline — no hardware or VISA required.
"""

import pytest
from keysight_dsox1200.instrument import _ch
from keysight_dsox1200 import (
    ChannelCoupling, AcquireType, TriggerSource, TriggerSlope,
    TriggerSweep, TimebaseMode, WaveformFormat, ValidationError,
)
from keysight_dsox1200.models import WaveformPreamble, ChannelConfig, ChannelUnit


# ------------------------------------------------------------------
# _ch() helper
# ------------------------------------------------------------------

@pytest.mark.parametrize("n,expected", [
    (1, "CHANnel1"),
    (2, "CHANnel2"),
    (3, "CHANnel3"),
    (4, "CHANnel4"),
])
def test_ch_valid(n, expected):
    assert _ch(n) == expected


@pytest.mark.parametrize("n", [0, 5, -1, 10])
def test_ch_invalid_raises(n):
    with pytest.raises(ValidationError):
        _ch(n)


# ------------------------------------------------------------------
# Enum round-trip: value should be valid SCPI short-form string
# ------------------------------------------------------------------

def test_coupling_str():
    for c in ChannelCoupling:
        assert isinstance(c.value, str)
        assert len(c.value) > 0


def test_trigger_source_str():
    for s in TriggerSource:
        assert "CHANnel" in s.value or s.value in ("EXTernal", "LINE")


def test_waveform_format_str():
    for f in WaveformFormat:
        assert f.value in ("BYTE", "WORD", "ASCii")


# ------------------------------------------------------------------
# WaveformPreamble edge cases
# ------------------------------------------------------------------

def test_preamble_single_point():
    raw = "0,0,1,1,1.0E-6,0.0,0,1.0E-3,0.0,0"
    p = WaveformPreamble.from_string(raw)
    assert p.points == 1
    t = p.time_axis()
    assert len(t) == 1
    assert t[0] == pytest.approx(0.0)


def test_preamble_volts_at_zero_offset():
    raw = "0,0,100,1,1.0E-9,0.0,0,0.001,0.0,0"
    p = WaveformPreamble.from_string(raw)
    import numpy as np
    raw_data = np.zeros(100, dtype=np.uint8)
    volts = p.to_volts(raw_data)
    assert all(v == pytest.approx(0.0) for v in volts)


def test_preamble_negative_x_origin():
    raw = "0,0,500,1,4.0E-9,-1.0E-6,0,0.001,0.0,128"
    p = WaveformPreamble.from_string(raw)
    t = p.time_axis()
    assert t[0] == pytest.approx(-1.0e-6, rel=1e-6)


# ------------------------------------------------------------------
# ChannelConfig dataclass defaults
# ------------------------------------------------------------------

def test_channel_config_defaults():
    cfg = ChannelConfig(channel=1)
    assert cfg.display is True
    assert cfg.coupling == ChannelCoupling.DC
    assert cfg.probe_attenuation == 1.0
    assert cfg.offset_v == 0.0
    assert cfg.invert is False
    assert cfg.label == ""
    assert cfg.unit == ChannelUnit.VOLT


def test_channel_config_custom():
    cfg = ChannelConfig(
        channel=3,
        display=False,
        coupling=ChannelCoupling.AC,
        probe_attenuation=10.0,
        range_v=4.0,
        offset_v=-0.5,
        invert=True,
        label="Error",
    )
    assert cfg.channel == 3
    assert cfg.coupling == ChannelCoupling.AC
    assert cfg.probe_attenuation == 10.0
    assert cfg.invert is True


# ------------------------------------------------------------------
# Acquire and timebase parameter ranges
# ------------------------------------------------------------------

@pytest.mark.parametrize("mode", list(TimebaseMode))
def test_timebase_mode_values_are_strings(mode):
    assert isinstance(mode.value, str)


@pytest.mark.parametrize("acq", list(AcquireType))
def test_acquire_type_values_are_strings(acq):
    assert isinstance(acq.value, str)
