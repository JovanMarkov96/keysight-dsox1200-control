"""Primary driver for Keysight InfiniiVision 1200 X-Series oscilloscopes.

Supported models: DSOX1202A/G, DSOX1204A/G, EDUX1052A/G.

Connection:
    scope = DSOX1200("USB0::0x2A8D::0x1797::XXXXXXXX::0::INSTR")
    scope = DSOX1200("TCPIP::192.168.1.10::inst0::INSTR")

Context-manager usage:
    with DSOX1200("USB0::...") as scope:
        scope.autoscale()
        wf = scope.capture_waveform(1)
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import List, Optional, Tuple, Union

import numpy as np

from .errors import CommandError, ConnectionError, TimeoutError, ValidationError
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
)

try:
    import pyvisa
    _HAS_PYVISA = True
except ImportError:
    _HAS_PYVISA = False


_VALID_CHANNELS = (1, 2, 3, 4)
_DEFAULT_TIMEOUT_MS = 10_000
_DIGITIZE_TIMEOUT_MS = 30_000


def _ch(n: int) -> str:
    if n not in _VALID_CHANNELS:
        raise ValidationError(f"Channel must be 1-4, got {n}")
    return f"CHANnel{n}"


class DSOX1200:
    """Driver for Keysight InfiniiVision 1200 X-Series oscilloscopes.

    All methods that set a parameter also have a corresponding query
    (same name, no arguments) so callers can verify the applied value.
    """

    def __init__(
        self,
        resource_name: str,
        timeout_ms: int = _DEFAULT_TIMEOUT_MS,
        resource_manager=None,
    ) -> None:
        """Open a VISA connection to the oscilloscope.

        Args:
            resource_name: VISA address string (USB or TCPIP).
            timeout_ms: I/O timeout in milliseconds.
            resource_manager: existing pyvisa.ResourceManager, or None.

        Raises:
            ImportError: if pyvisa is not installed.
            ConnectionError: if the resource cannot be opened.
        """
        if not _HAS_PYVISA:
            raise ImportError(
                "pyvisa is required. Install with: pip install pyvisa pyvisa-py"
            )
        try:
            rm = resource_manager or pyvisa.ResourceManager()
            self._resource = rm.open_resource(resource_name)
            self._resource.timeout = timeout_ms
            # IEEE 488.2 line terminator expected by the scope
            self._resource.read_termination = "\n"
            self._resource.write_termination = "\n"
        except Exception as exc:
            raise ConnectionError(f"Could not open {resource_name}: {exc}") from exc

        self._resource_name = resource_name
        self._timeout_ms = timeout_ms

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DSOX1200":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def close(self) -> None:
        """Release the VISA resource."""
        try:
            self._resource.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Low-level transport
    # ------------------------------------------------------------------

    def write(self, command: str) -> None:
        """Send a SCPI command (no response expected)."""
        self._resource.write(command)

    def query(self, command: str) -> str:
        """Send a query and return the stripped string response."""
        return self._resource.query(command).strip()

    def query_float(self, command: str) -> float:
        return float(self.query(command))

    def query_int(self, command: str) -> int:
        return int(self.query(command))

    def query_binary(self, command: str) -> np.ndarray:
        """Query binary block data and return as uint8 numpy array."""
        return np.frombuffer(
            self._resource.query_binary_values(
                command, datatype="B", is_big_endian=False, container=bytes
            ),
            dtype=np.uint8,
        )

    def query_binary_word(self, command: str) -> np.ndarray:
        """Query 16-bit signed word binary block data."""
        return np.array(
            self._resource.query_binary_values(
                command, datatype="h", is_big_endian=True
            ),
            dtype=np.int16,
        )

    def check_errors(self) -> None:
        """Read the error queue and raise CommandError if any errors are present."""
        while True:
            response = self.query(":SYSTem:ERRor?")
            code_str, _, msg = response.partition(",")
            code = int(code_str.strip())
            if code == 0:
                break
            raise CommandError(code, msg.strip().strip('"'))

    # ------------------------------------------------------------------
    # IEEE 488.2 Common Commands
    # ------------------------------------------------------------------

    def identify(self) -> str:
        """Query *IDN? — return manufacturer/model/serial/firmware string."""
        return self.query("*IDN?")

    def reset(self) -> None:
        """*RST — reset instrument to factory default state."""
        self.write("*RST")
        time.sleep(0.5)

    def clear_status(self) -> None:
        """*CLS — clear status registers and error queue."""
        self.write("*CLS")

    def operation_complete(self) -> bool:
        """*OPC? — return True once all pending operations are complete."""
        return self.query("*OPC?") == "1"

    def wait(self) -> None:
        """*WAI — prevent instrument from processing further commands until done."""
        self.write("*WAI")

    def trigger(self) -> None:
        """*TRG — issue a bus trigger."""
        self.write("*TRG")

    def save_state(self, slot: int) -> None:
        """*SAV <slot> — save current state to internal memory slot (1-10)."""
        self.write(f"*SAV {slot}")

    def recall_state(self, slot: int) -> None:
        """*RCL <slot> — recall state from internal memory slot (1-10)."""
        self.write(f"*RCL {slot}")

    def self_test(self) -> int:
        """*TST? — run self-test; return 0 on pass."""
        return self.query_int("*TST?")

    def get_options(self) -> str:
        """*OPT? — return installed options string."""
        return self.query("*OPT?")

    # ------------------------------------------------------------------
    # Root-level commands
    # ------------------------------------------------------------------

    def autoscale(self) -> None:
        """:AUToscale — auto-configure vertical, timebase, and trigger."""
        self.write(":AUToscale")
        time.sleep(1.0)

    def run(self) -> None:
        """:RUN — start continuous acquisitions."""
        self.write(":RUN")

    def stop(self) -> None:
        """:STOP — halt acquisitions."""
        self.write(":STOP")

    def single(self) -> None:
        """:SINGle — arm for one acquisition then stop."""
        self.write(":SINGle")

    def digitize(self, *channels: int) -> None:
        """:DIGitize — trigger a single acquisition of the specified channels.

        Stops the scope, clears waveform memory, acquires until full, then stops.
        Must be used with TIMebase:MODE MAIN.

        Args:
            channels: channel numbers to digitize (1-4). Empty = all displayed.
        """
        if channels:
            src = ", ".join(_ch(c) for c in channels)
            self.write(f":DIGitize {src}")
        else:
            self.write(":DIGitize")

    def view(self, channel: int) -> None:
        """:VIEW CHANneln — turn on display for a channel."""
        self.write(f":VIEW {_ch(channel)}")

    def blank(self, channel: int) -> None:
        """:BLANk CHANneln — turn off display for a channel."""
        self.write(f":BLANk {_ch(channel)}")

    # ------------------------------------------------------------------
    # :CHANnel<n> subsystem
    # ------------------------------------------------------------------

    def channel_display(self, channel: int, on: bool) -> None:
        self.write(f":{_ch(channel)}:DISPlay {'ON' if on else 'OFF'}")

    def channel_display_query(self, channel: int) -> bool:
        return self.query(f":{_ch(channel)}:DISPlay?") == "1"

    def channel_coupling(self, channel: int, coupling: ChannelCoupling) -> None:
        self.write(f":{_ch(channel)}:COUPling {coupling.value}")

    def channel_coupling_query(self, channel: int) -> str:
        return self.query(f":{_ch(channel)}:COUPling?")

    def channel_probe(self, channel: int, attenuation: float) -> None:
        """Set probe attenuation ratio (e.g. 10 for 10:1 probe)."""
        self.write(f":{_ch(channel)}:PROBe {attenuation:g}")

    def channel_probe_query(self, channel: int) -> float:
        return self.query_float(f":{_ch(channel)}:PROBe?")

    def channel_range(self, channel: int, full_scale_volts: float) -> None:
        """Set full-scale vertical range in volts (8 × V/div)."""
        self.write(f":{_ch(channel)}:RANGe {full_scale_volts:g}")

    def channel_range_query(self, channel: int) -> float:
        return self.query_float(f":{_ch(channel)}:RANGe?")

    def channel_scale(self, channel: int, volts_per_div: float) -> None:
        """Set vertical scale in V/div."""
        self.write(f":{_ch(channel)}:SCALe {volts_per_div:g}")

    def channel_scale_query(self, channel: int) -> float:
        return self.query_float(f":{_ch(channel)}:SCALe?")

    def channel_offset(self, channel: int, offset_volts: float) -> None:
        """Set vertical offset (voltage at centre screen)."""
        self.write(f":{_ch(channel)}:OFFSet {offset_volts:g}")

    def channel_offset_query(self, channel: int) -> float:
        return self.query_float(f":{_ch(channel)}:OFFSet?")

    def channel_invert(self, channel: int, invert: bool) -> None:
        self.write(f":{_ch(channel)}:INVert {'ON' if invert else 'OFF'}")

    def channel_invert_query(self, channel: int) -> bool:
        return self.query(f":{_ch(channel)}:INVert?") == "1"

    def channel_label(self, channel: int, label: str) -> None:
        self.write(f':{_ch(channel)}:LABel "{label}"')

    def channel_label_query(self, channel: int) -> str:
        return self.query(f":{_ch(channel)}:LABel?").strip('"')

    def channel_bwlimit(self, channel: int, on: bool) -> None:
        """Enable 20 MHz bandwidth limit filter."""
        self.write(f":{_ch(channel)}:BWLimit {'ON' if on else 'OFF'}")

    def channel_bwlimit_query(self, channel: int) -> bool:
        return self.query(f":{_ch(channel)}:BWLimit?") == "1"

    def channel_unit(self, channel: int, unit: ChannelUnit) -> None:
        self.write(f":{_ch(channel)}:UNITs {unit.value}")

    def channel_unit_query(self, channel: int) -> str:
        return self.query(f":{_ch(channel)}:UNITs?")

    def configure_channel(
        self,
        channel: int,
        *,
        coupling: Optional[ChannelCoupling] = None,
        probe: Optional[float] = None,
        range_v: Optional[float] = None,
        scale_v: Optional[float] = None,
        offset_v: Optional[float] = None,
        invert: Optional[bool] = None,
        label: Optional[str] = None,
        display: Optional[bool] = None,
        bwlimit: Optional[bool] = None,
        unit: Optional[ChannelUnit] = None,
    ) -> None:
        """Convenience: set multiple channel parameters in one call."""
        if display is not None:
            self.channel_display(channel, display)
        if coupling is not None:
            self.channel_coupling(channel, coupling)
        if probe is not None:
            self.channel_probe(channel, probe)
        if range_v is not None:
            self.channel_range(channel, range_v)
        if scale_v is not None:
            self.channel_scale(channel, scale_v)
        if offset_v is not None:
            self.channel_offset(channel, offset_v)
        if invert is not None:
            self.channel_invert(channel, invert)
        if label is not None:
            self.channel_label(channel, label)
        if bwlimit is not None:
            self.channel_bwlimit(channel, bwlimit)
        if unit is not None:
            self.channel_unit(channel, unit)

    # ------------------------------------------------------------------
    # :TIMebase subsystem
    # ------------------------------------------------------------------

    def timebase_mode(self, mode: TimebaseMode) -> None:
        self.write(f":TIMebase:MODE {mode.value}")

    def timebase_mode_query(self) -> str:
        return self.query(":TIMebase:MODE?")

    def timebase_range(self, full_scale_seconds: float) -> None:
        """Set horizontal full-scale time range (10 × time/div)."""
        self.write(f":TIMebase:RANGe {full_scale_seconds:g}")

    def timebase_range_query(self) -> float:
        return self.query_float(":TIMebase:RANGe?")

    def timebase_scale(self, seconds_per_div: float) -> None:
        """Set horizontal scale in s/div."""
        self.write(f":TIMebase:SCALe {seconds_per_div:g}")

    def timebase_scale_query(self) -> float:
        return self.query_float(":TIMebase:SCALe?")

    def timebase_position(self, seconds: float) -> None:
        """Set trigger position (delay) relative to time reference."""
        self.write(f":TIMebase:POSition {seconds:g}")

    def timebase_position_query(self) -> float:
        return self.query_float(":TIMebase:POSition?")

    def timebase_reference(self, ref: str = "CENTer") -> None:
        """Set time reference point: LEFT, CENTer, or RIGHT."""
        self.write(f":TIMebase:REFerence {ref}")

    def timebase_reference_query(self) -> str:
        return self.query(":TIMebase:REFerence?")

    def configure_timebase(
        self,
        *,
        mode: Optional[TimebaseMode] = None,
        range_s: Optional[float] = None,
        scale_s: Optional[float] = None,
        position_s: Optional[float] = None,
        reference: Optional[str] = None,
    ) -> None:
        """Convenience: set multiple timebase parameters in one call."""
        if mode is not None:
            self.timebase_mode(mode)
        if range_s is not None:
            self.timebase_range(range_s)
        if scale_s is not None:
            self.timebase_scale(scale_s)
        if position_s is not None:
            self.timebase_position(position_s)
        if reference is not None:
            self.timebase_reference(reference)

    # ------------------------------------------------------------------
    # :TRIGger subsystem
    # ------------------------------------------------------------------

    def trigger_sweep(self, sweep: TriggerSweep) -> None:
        self.write(f":TRIGger:SWEep {sweep.value}")

    def trigger_sweep_query(self) -> str:
        return self.query(":TRIGger:SWEep?")

    def trigger_holdoff(self, seconds: float) -> None:
        self.write(f":TRIGger:HOLDoff {seconds:g}")

    def trigger_holdoff_query(self) -> float:
        return self.query_float(":TRIGger:HOLDoff?")

    def trigger_hfreject(self, on: bool) -> None:
        """Enable high-frequency noise rejection on trigger signal."""
        self.write(f":TRIGger:HFReject {'ON' if on else 'OFF'}")

    def trigger_nreject(self, on: bool) -> None:
        """Enable noise rejection (narrow pulse filter) on trigger signal."""
        self.write(f":TRIGger:NREJect {'ON' if on else 'OFF'}")

    def trigger_force(self) -> None:
        """:TRIGger:FORCe — force a trigger event immediately."""
        self.write(":TRIGger:FORCe")

    # Edge trigger
    def trigger_edge_source(self, source: TriggerSource) -> None:
        self.write(f":TRIGger[:EDGE]:SOURce {source.value}")

    def trigger_edge_source_query(self) -> str:
        return self.query(":TRIGger[:EDGE]:SOURce?")

    def trigger_edge_slope(self, slope: TriggerSlope) -> None:
        self.write(f":TRIGger[:EDGE]:SLOPe {slope.value}")

    def trigger_edge_slope_query(self) -> str:
        return self.query(":TRIGger[:EDGE]:SLOPe?")

    def trigger_edge_level(self, volts: float) -> None:
        self.write(f":TRIGger[:EDGE]:LEVel {volts:g}")

    def trigger_edge_level_query(self) -> float:
        return self.query_float(":TRIGger[:EDGE]:LEVel?")

    def trigger_edge_coupling(self, coupling: str = "DC") -> None:
        """Set edge trigger coupling: DC, AC, LFReject, HFReject."""
        self.write(f":TRIGger[:EDGE]:COUPling {coupling}")

    def configure_trigger_edge(
        self,
        source: TriggerSource,
        level_v: float,
        slope: TriggerSlope = TriggerSlope.POSITIVE,
        sweep: TriggerSweep = TriggerSweep.NORMAL,
        coupling: str = "DC",
    ) -> None:
        """Convenience: configure edge trigger in one call."""
        self.trigger_edge_source(source)
        self.trigger_edge_level(level_v)
        self.trigger_edge_slope(slope)
        self.trigger_sweep(sweep)
        self.trigger_edge_coupling(coupling)

    # Trigger level auto-setup
    def trigger_level_asetup(self) -> None:
        """:TRIGger:LEVel:ASETup — auto-set trigger level to 50% of signal."""
        self.write(":TRIGger:LEVel:ASETup")

    # ------------------------------------------------------------------
    # :ACQuire subsystem
    # ------------------------------------------------------------------

    def acquire_type(self, acq_type: AcquireType) -> None:
        self.write(f":ACQuire:TYPE {acq_type.value}")

    def acquire_type_query(self) -> str:
        return self.query(":ACQuire:TYPE?")

    def acquire_count(self, n: int) -> None:
        """Set number of averages (2-65536) when TYPE is AVERage."""
        self.write(f":ACQuire:COUNt {n}")

    def acquire_count_query(self) -> int:
        return self.query_int(":ACQuire:COUNt?")

    def acquire_points(self, n: int) -> None:
        """Set number of data points acquired per waveform."""
        self.write(f":ACQuire:POINts {n}")

    def acquire_points_query(self) -> int:
        return self.query_int(":ACQuire:POINts?")

    def acquire_srate_query(self) -> float:
        """Query actual sample rate (read-only, set by scope based on timebase)."""
        return self.query_float(":ACQuire:SRATe?")

    def acquire_complete(self) -> int:
        """:ACQuire:COMPlete? — percentage of required waveforms acquired."""
        return self.query_int(":ACQuire:COMPlete?")

    def configure_acquire(
        self,
        *,
        acq_type: Optional[AcquireType] = None,
        count: Optional[int] = None,
        points: Optional[int] = None,
    ) -> None:
        if acq_type is not None:
            self.acquire_type(acq_type)
        if count is not None:
            self.acquire_count(count)
        if points is not None:
            self.acquire_points(points)

    # ------------------------------------------------------------------
    # :WAVeform subsystem — waveform download
    # ------------------------------------------------------------------

    def waveform_source(self, source: WaveformSource) -> None:
        self.write(f":WAVeform:SOURce {source.value}")

    def waveform_format(self, fmt: WaveformFormat) -> None:
        self.write(f":WAVeform:FORMat {fmt.value}")

    def waveform_points(self, n: int) -> None:
        """Set number of points to transfer (up to acquire:points max)."""
        self.write(f":WAVeform:POINts {n}")

    def waveform_preamble(self) -> WaveformPreamble:
        """:WAVeform:PREamble? — parse and return scaling parameters."""
        raw = self.query(":WAVeform:PREamble?")
        return WaveformPreamble.from_string(raw)

    def waveform_data_raw(self) -> np.ndarray:
        """:WAVeform:DATA? — return raw uint8 data (format must be BYTE)."""
        return self.query_binary(":WAVeform:DATA?")

    def capture_waveform(
        self,
        channel: int,
        points: Optional[int] = None,
        digitize: bool = True,
        fmt: WaveformFormat = WaveformFormat.BYTE,
    ) -> WaveformData:
        """Acquire and return a fully scaled waveform from one channel.

        Args:
            channel: channel number 1-4.
            points: number of points (None = use current acquire:points setting).
            digitize: if True, send :DIGitize first to capture fresh data.
            fmt: wire format. BYTE is fastest; WORD gives full 16-bit resolution.

        Returns:
            WaveformData with .time (s) and .voltage (V) numpy arrays.
        """
        if digitize:
            prev_timeout = self._resource.timeout
            self._resource.timeout = _DIGITIZE_TIMEOUT_MS
            try:
                self.digitize(channel)
            finally:
                self._resource.timeout = prev_timeout

        src = WaveformSource(f"CHANnel{channel}")
        self.waveform_source(src)
        self.waveform_format(fmt)
        if points is not None:
            self.waveform_points(points)

        preamble = self.waveform_preamble()

        if fmt == WaveformFormat.BYTE:
            raw = self.waveform_data_raw()
        elif fmt == WaveformFormat.WORD:
            raw = self.query_binary_word(":WAVeform:DATA?")
        else:
            asc = self.query(":WAVeform:DATA?")
            raw = np.array([float(v) for v in asc.split(",")], dtype=float)
            return WaveformData(
                time=preamble.time_axis(),
                voltage=raw,
                preamble=preamble,
                source=f"CHANnel{channel}",
            )

        return WaveformData(
            time=preamble.time_axis(),
            voltage=preamble.to_volts(raw),
            preamble=preamble,
            source=f"CHANnel{channel}",
        )

    def capture_all_channels(
        self, channels: List[int] = None, points: Optional[int] = None
    ) -> dict:
        """Digitize and return waveforms for multiple channels.

        Args:
            channels: list of channel numbers. Defaults to [1, 2, 3, 4].
            points: points per channel.

        Returns:
            dict mapping channel number to WaveformData.
        """
        if channels is None:
            channels = [1, 2, 3, 4]

        prev_timeout = self._resource.timeout
        self._resource.timeout = _DIGITIZE_TIMEOUT_MS
        try:
            self.digitize(*channels)
        finally:
            self._resource.timeout = prev_timeout

        result = {}
        for ch in channels:
            result[ch] = self.capture_waveform(ch, points=points, digitize=False)
        return result

    # ------------------------------------------------------------------
    # :MEASure subsystem — automatic parametric measurements
    # ------------------------------------------------------------------

    def _measure_source(self, source: Optional[MeasureSource]) -> str:
        return f" {source.value}" if source else ""

    def measure_frequency(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:FREQuency?{self._measure_source(source)}")

    def measure_period(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:PERiod?{self._measure_source(source)}")

    def measure_duty_cycle(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:DUTYcycle?{self._measure_source(source)}")

    def measure_vmax(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:VMAX?{self._measure_source(source)}")

    def measure_vmin(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:VMIN?{self._measure_source(source)}")

    def measure_vpp(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:VPP?{self._measure_source(source)}")

    def measure_vrms(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:VRMS?{self._measure_source(source)}")

    def measure_vaverage(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:VAVerage?{self._measure_source(source)}")

    def measure_vamplitude(self, source: Optional[MeasureSource] = None) -> float:
        """Vamp = Vtop - Vbase."""
        return self.query_float(f":MEASure:VAMPlitude?{self._measure_source(source)}")

    def measure_vtop(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:VTOP?{self._measure_source(source)}")

    def measure_vbase(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:VBASe?{self._measure_source(source)}")

    def measure_risetime(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:RISetime?{self._measure_source(source)}")

    def measure_falltime(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:FALLtime?{self._measure_source(source)}")

    def measure_phase(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:PHASe?{self._measure_source(source)}")

    def measure_delay(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:DELay?{self._measure_source(source)}")

    def measure_nwidth(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:NWIDth?{self._measure_source(source)}")

    def measure_pwidth(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:PWIDth?{self._measure_source(source)}")

    def measure_overshoot(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:OVERshoot?{self._measure_source(source)}")

    def measure_preshoot(self, source: Optional[MeasureSource] = None) -> float:
        return self.query_float(f":MEASure:PREShoot?{self._measure_source(source)}")

    def measure_counter(self, source: Optional[MeasureSource] = None) -> float:
        """Hardware counter frequency measurement (more accurate than FFT)."""
        return self.query_float(f":MEASure:COUNter?{self._measure_source(source)}")

    def measure_clear(self) -> None:
        """:MEASure:CLEar — remove all on-screen measurements."""
        self.write(":MEASure:CLEar")

    def measure_statistics_reset(self) -> None:
        self.write(":MEASure:STATistics:RESet")

    def measure_statistics_display(self, on: bool) -> None:
        self.write(f":MEASure:STATistics:DISPlay {'ON' if on else 'OFF'}")

    # ------------------------------------------------------------------
    # :MARKer subsystem — X/Y cursors
    # ------------------------------------------------------------------

    def marker_mode(self, mode: str) -> None:
        """Set marker mode: OFF, MANual, MEASure, or WAVeform."""
        self.write(f":MARKer:MODE {mode}")

    def marker_mode_query(self) -> str:
        return self.query(":MARKer:MODE?")

    def marker_x1_position(self, seconds: float) -> None:
        self.write(f":MARKer:X1Position {seconds:g}")

    def marker_x1_position_query(self) -> float:
        return self.query_float(":MARKer:X1Position?")

    def marker_x2_position(self, seconds: float) -> None:
        self.write(f":MARKer:X2Position {seconds:g}")

    def marker_x2_position_query(self) -> float:
        return self.query_float(":MARKer:X2Position?")

    def marker_xdelta_query(self) -> float:
        """X2 - X1 time difference."""
        return self.query_float(":MARKer:XDELta?")

    def marker_ydelta_query(self) -> float:
        """Y2 - Y1 voltage difference."""
        return self.query_float(":MARKer:YDELta?")

    # ------------------------------------------------------------------
    # :DISPlay subsystem
    # ------------------------------------------------------------------

    def display_persistence(self, seconds: Union[float, str]) -> None:
        """Set persistence: float seconds, 'INFinite', or 'OFF'."""
        self.write(f":DISPlay:PERSistence {seconds}")

    def display_persistence_query(self) -> str:
        return self.query(":DISPlay:PERSistence?")

    def display_vectors(self, on: bool) -> None:
        """Connect sample points with vectors (on) or show dots only (off)."""
        self.write(f":DISPlay:VECTors {'ON' if on else 'OFF'}")

    def display_labels(self, on: bool) -> None:
        self.write(f":DISPlay:LABel {'ON' if on else 'OFF'}")

    def display_clear(self) -> None:
        """:DISPlay:CLEar — clear persistence display."""
        self.write(":DISPlay:CLEar")

    def display_intensity(self, percent: int) -> None:
        """Set waveform intensity 0-100%."""
        self.write(f":DISPlay:INTensity:WAVeform {percent}")

    # ------------------------------------------------------------------
    # :SYSTem subsystem
    # ------------------------------------------------------------------

    def system_error_query(self) -> Tuple[int, str]:
        """Return (code, message) from error queue. code=0 means no error."""
        response = self.query(":SYSTem:ERRor?")
        code_str, _, msg = response.partition(",")
        return int(code_str.strip()), msg.strip().strip('"')

    def system_date_query(self) -> str:
        return self.query(":SYSTem:DATE?")

    def system_time_query(self) -> str:
        return self.query(":SYSTem:TIME?")

    def system_setup_query(self) -> bytes:
        """Return the full instrument setup as a binary learn string."""
        return self._resource.query_binary_values(
            ":SYSTem:SETup?", datatype="B", container=bytes
        )

    def system_setup_restore(self, setup: bytes) -> None:
        """Restore a previously saved setup learn string."""
        self._resource.write_binary_values(":SYSTem:SETup ", setup, datatype="B")

    def system_lock(self, lock: bool) -> None:
        """Lock (True) or unlock (False) the front-panel controls."""
        self.write(f":SYSTem:LOCK {'ON' if lock else 'OFF'}")

    # ------------------------------------------------------------------
    # :HARDcopy — screen capture
    # ------------------------------------------------------------------

    def screenshot(self, filename: str = "screen.png") -> bytes:
        """Capture the current screen as PNG and return the raw bytes.

        Also optionally save to a local file.

        Args:
            filename: local filename to save to ('' to skip saving).

        Returns:
            PNG image bytes.
        """
        self.write(":HARDcopy:INKSaver OFF")
        data = self._resource.query_binary_values(
            ":DISPlay:DATA? PNG, COLor", datatype="B", container=bytes
        )
        if filename:
            with open(filename, "wb") as f:
                f.write(data)
        return data

    # ------------------------------------------------------------------
    # :SAVE / :RECall subsystem (instrument-side file operations)
    # ------------------------------------------------------------------

    def save_setup(self, filename: str) -> None:
        """Save current setup to a file on the instrument's USB drive."""
        self.write(f':SAVE:SETup "{filename}"')

    def save_waveform(
        self, filename: str, source: Optional[WaveformSource] = None, fmt: str = "CSV"
    ) -> None:
        """Save waveform data to a file on the instrument's USB drive.

        Args:
            filename: destination path on instrument USB drive.
            source: waveform source (None = use current :WAVeform:SOURce).
            fmt: CSV, BIN, or ASC.
        """
        if source:
            self.waveform_source(source)
        self.write(f':SAVE:WAVeform:FORMat {fmt}')
        self.write(f':SAVE:WAVeform "{filename}"')

    def save_image(self, filename: str) -> None:
        """Save screen image to a file on the instrument's USB drive."""
        self.write(f':SAVE:IMAGe "{filename}"')

    # ------------------------------------------------------------------
    # :FFT subsystem
    # ------------------------------------------------------------------

    def fft_display(self, on: bool) -> None:
        self.write(f":FFT:DISPlay {'ON' if on else 'OFF'}")

    def fft_source(self, channel: int) -> None:
        self.write(f":FFT:SOURce1 {_ch(channel)}")

    def fft_span(self, hz: float) -> None:
        self.write(f":FFT:SPAN {hz:g}")

    def fft_span_query(self) -> float:
        return self.query_float(":FFT:SPAN?")

    def fft_center(self, hz: float) -> None:
        self.write(f":FFT:CENTer {hz:g}")

    def fft_window(self, window: str) -> None:
        """Set FFT window: HANNing, FLATtop, RECTangular, BHARris."""
        self.write(f":FFT:WINDow {window}")

    def fft_scale(self, db_div: float) -> None:
        self.write(f":FFT:SCALe {db_div:g}")

    def fft_reference(self, db: float) -> None:
        self.write(f":FFT:REFerence {db:g}")

    # ------------------------------------------------------------------
    # :DVM subsystem — digital voltmeter
    # ------------------------------------------------------------------

    def dvm_enable(self, on: bool) -> None:
        self.write(f":DVM:ENABle {'ON' if on else 'OFF'}")

    def dvm_source(self, channel: int) -> None:
        self.write(f":DVM:SOURce {_ch(channel)}")

    def dvm_mode(self, mode: str) -> None:
        """Set DVM mode: DC, ACRMS, FREQ, or OFF."""
        self.write(f":DVM:MODE {mode}")

    def dvm_current_query(self) -> float:
        """:DVM:CURRent? — return current DVM reading."""
        return self.query_float(":DVM:CURRent?")

    # ------------------------------------------------------------------
    # Utility / convenience
    # ------------------------------------------------------------------

    def wait_for_acquisition(self, timeout_s: float = 30.0, poll_s: float = 0.1) -> None:
        """Block until :ACQuire:COMPlete? returns 100 (fully acquired).

        Args:
            timeout_s: maximum time to wait in seconds.
            poll_s: polling interval in seconds.

        Raises:
            TimeoutError: if acquisition is not complete within timeout.
        """
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.acquire_complete() == 100:
                return
            time.sleep(poll_s)
        raise TimeoutError(f"Acquisition not complete within {timeout_s} s")

    @contextmanager
    def acquisition(
        self,
        acq_type: AcquireType = AcquireType.NORMAL,
        count: int = 1,
        timeout_s: float = 30.0,
    ):
        """Context manager: configure, trigger single acquisition, yield self.

        Usage:
            with scope.acquisition(AcquireType.AVERAGE, count=16) as scope:
                wf = scope.capture_waveform(1, digitize=False)
        """
        self.configure_acquire(acq_type=acq_type, count=count)
        self.timebase_mode(TimebaseMode.MAIN)
        self.single()
        self.wait_for_acquisition(timeout_s=timeout_s)
        yield self
