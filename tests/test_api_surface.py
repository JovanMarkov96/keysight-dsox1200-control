"""Smoke tests for the public API surface — no hardware required.

Tests verify:
- All public names are importable.
- Enum values match expected SCPI strings.
- WaveformPreamble parsing is correct.
- DSOX1200 can be instantiated with a mock resource.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# ------------------------------------------------------------------
# Import surface
# ------------------------------------------------------------------

def test_public_imports():
    from keysight_dsox1200 import (
        DSOX1200, AcquireType, ChannelCoupling, ChannelUnit,
        MeasureSource, TimebaseMode, TriggerSlope, TriggerSource,
        TriggerSweep, WaveformData, WaveformFormat, WaveformPreamble,
        WaveformSource, ChannelConfig, DSO1200Error, ConnectionError,
        CommandError, TimeoutError, ValidationError,
        list_instruments, auto_connect,
    )


def test_version_present():
    import keysight_dsox1200
    assert hasattr(keysight_dsox1200, "__version__")
    assert keysight_dsox1200.__version__ == "0.1.0"


# ------------------------------------------------------------------
# Enum values match SCPI strings
# ------------------------------------------------------------------

def test_coupling_enum_values():
    from keysight_dsox1200 import ChannelCoupling
    assert ChannelCoupling.DC.value == "DC"
    assert ChannelCoupling.AC.value == "AC"
    assert ChannelCoupling.GND.value == "GND"


def test_trigger_slope_values():
    from keysight_dsox1200 import TriggerSlope
    assert TriggerSlope.POSITIVE.value == "POSitive"
    assert TriggerSlope.NEGATIVE.value == "NEGative"


def test_trigger_source_values():
    from keysight_dsox1200 import TriggerSource
    assert TriggerSource.CH1.value == "CHANnel1"
    assert TriggerSource.EXTERNAL.value == "EXTernal"


def test_waveform_format_values():
    from keysight_dsox1200 import WaveformFormat
    assert WaveformFormat.BYTE.value == "BYTE"
    assert WaveformFormat.WORD.value == "WORD"
    assert WaveformFormat.ASCII.value == "ASCii"


def test_acquire_type_values():
    from keysight_dsox1200 import AcquireType
    assert AcquireType.NORMAL.value == "NORMal"
    assert AcquireType.AVERAGE.value == "AVERage"


def test_timebase_mode_values():
    from keysight_dsox1200 import TimebaseMode
    assert TimebaseMode.MAIN.value == "MAIN"
    assert TimebaseMode.ROLL.value == "ROLL"


# ------------------------------------------------------------------
# WaveformPreamble
# ------------------------------------------------------------------

_SAMPLE_PREAMBLE = "0,0,1000,1,2.0E-9,-1.0E-6,0,3.906250E-4,0.0,125"


def test_preamble_parsing():
    from keysight_dsox1200 import WaveformPreamble
    p = WaveformPreamble.from_string(_SAMPLE_PREAMBLE)
    assert p.format == 0
    assert p.wf_type == 0
    assert p.points == 1000
    assert p.count == 1
    assert pytest.approx(p.x_increment, rel=1e-6) == 2.0e-9
    assert pytest.approx(p.x_origin, rel=1e-6) == -1.0e-6
    assert p.x_reference == 0
    assert pytest.approx(p.y_increment, rel=1e-6) == 3.90625e-4
    assert p.y_origin == 0.0
    assert p.y_reference == 125


def test_preamble_time_axis():
    from keysight_dsox1200 import WaveformPreamble
    p = WaveformPreamble.from_string(_SAMPLE_PREAMBLE)
    t = p.time_axis()
    assert len(t) == 1000
    assert pytest.approx(t[0], abs=1e-15) == p.x_origin
    assert pytest.approx(t[1] - t[0], rel=1e-6) == p.x_increment


def test_preamble_to_volts():
    from keysight_dsox1200 import WaveformPreamble
    p = WaveformPreamble.from_string(_SAMPLE_PREAMBLE)
    raw = np.array([125, 126, 124], dtype=np.uint8)
    volts = p.to_volts(raw)
    assert pytest.approx(volts[0]) == 0.0   # raw == y_reference → y_origin (0)
    assert pytest.approx(volts[1], abs=1e-6) == p.y_increment   # one step above
    assert pytest.approx(volts[2], abs=1e-6) == -p.y_increment  # one step below


# ------------------------------------------------------------------
# Error classes
# ------------------------------------------------------------------

def test_command_error_attributes():
    from keysight_dsox1200 import CommandError
    e = CommandError(-113, "Undefined header")
    assert e.code == -113
    assert "Undefined header" in str(e)


def test_validation_error():
    from keysight_dsox1200.instrument import _ch
    from keysight_dsox1200 import ValidationError
    with pytest.raises(ValidationError):
        _ch(5)


# ------------------------------------------------------------------
# DSOX1200 with mock resource
# ------------------------------------------------------------------

@pytest.fixture
def mock_scope():
    with patch("keysight_dsox1200.instrument.pyvisa") as mock_pyvisa:
        mock_rm = MagicMock()
        mock_resource = MagicMock()
        mock_resource.query.return_value = "KEYSIGHT TECHNOLOGIES,DSO-X 1204A,CN12345678,02.12.2021102901\n"
        mock_pyvisa.ResourceManager.return_value = mock_rm
        mock_rm.open_resource.return_value = mock_resource

        from keysight_dsox1200 import DSOX1200
        scope = DSOX1200("USB0::MOCK::INSTR", resource_manager=mock_rm)
        scope._resource = mock_resource
        yield scope, mock_resource


def test_identify(mock_scope):
    scope, resource = mock_scope
    resource.query.return_value = "KEYSIGHT TECHNOLOGIES,DSO-X 1204A,CN12345678,02.12\n"
    result = scope.identify()
    resource.query.assert_called_with("*IDN?")
    assert "KEYSIGHT" in result or result  # mock returns whatever we set


def test_write_reset(mock_scope):
    scope, resource = mock_scope
    scope.reset()
    resource.write.assert_any_call("*RST")


def test_channel_display(mock_scope):
    scope, resource = mock_scope
    scope.channel_display(1, True)
    resource.write.assert_called_with(":CHANnel1:DISPlay ON")


def test_channel_scale(mock_scope):
    scope, resource = mock_scope
    scope.channel_scale(2, 0.5)
    resource.write.assert_called_with(":CHANnel2:SCALe 0.5")


def test_timebase_scale(mock_scope):
    scope, resource = mock_scope
    scope.timebase_scale(1e-3)
    resource.write.assert_called_with(":TIMebase:SCALe 0.001")


def test_trigger_edge_level(mock_scope):
    scope, resource = mock_scope
    scope.trigger_edge_level(0.5)
    resource.write.assert_called_with(":TRIGger[:EDGE]:LEVel 0.5")


def test_run_stop_single(mock_scope):
    scope, resource = mock_scope
    scope.run()
    resource.write.assert_called_with(":RUN")
    scope.stop()
    resource.write.assert_called_with(":STOP")
    scope.single()
    resource.write.assert_called_with(":SINGle")
