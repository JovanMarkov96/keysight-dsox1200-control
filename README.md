# keysight-dsox1200-control

Python driver and standalone GUI for **Keysight InfiniiVision 1200 X-Series** oscilloscopes.

Supported models: **DSOX1202A**, **DSOX1202G**, **DSOX1204A**, **DSOX1204G**, **EDUX1052A**, **EDUX1052G**

---

## Features

| Subsystem | Implemented |
|-----------|-------------|
| Connect via USB or LAN (VISA) | Yes |
| Channel setup (coupling, scale, offset, probe, invert, label, BW limit) | Yes |
| Timebase (scale, position, mode, reference) | Yes |
| Edge trigger (source, level, slope, sweep, coupling, force, 50% auto-level) | Yes |
| Acquisition (normal, average, hi-res, peak; point count) | Yes |
| Waveform download with auto-scaling (`time`, `voltage` arrays) | Yes |
| Automatic measurements (Vpp, Vrms, Vmax, frequency, rise time, …) | Yes |
| Markers / cursors (X1, X2, delta-T, delta-V) | Yes |
| FFT control | Yes |
| DVM (digital voltmeter) | Yes |
| Screenshot capture to PNG | Yes |
| Save/recall waveform and setup | Yes |
| System error queue readback | Yes |
| Standalone GUI (tkinter + matplotlib) | Yes |

---

## Installation

```bash
pip install keysight-dsox1200-control
```

Or install from source:

```bash
git clone https://github.com/JovanMarkov96/keysight-dsox1200-control.git
cd keysight-dsox1200-control
pip install -e ".[dev]"
```

### Requirements

- Python ≥ 3.8
- `pyvisa` ≥ 1.12
- `pyvisa-py` (pure-Python VISA backend, no NI-VISA required)  
  *Or* Keysight IO Libraries Suite for NI-VISA
- `numpy` ≥ 1.20
- `matplotlib` ≥ 3.4 (for GUI and plot examples)

---

## Quick Start

```python
from keysight_dsox1200 import DSOX1200, ChannelCoupling, TriggerSource, TriggerSlope

# Connect (USB or LAN)
with DSOX1200("USB0::0x2A8D::0x1797::MYSERIAL::0::INSTR") as scope:
    print(scope.identify())

    # Configure
    scope.reset()
    scope.configure_channel(1, coupling=ChannelCoupling.DC, scale_v=0.5, probe=1.0)
    scope.configure_timebase(scale_s=1e-3)
    scope.configure_trigger_edge(
        source=TriggerSource.CH1,
        level_v=0.0,
        slope=TriggerSlope.POSITIVE,
    )

    # Capture waveform
    wf = scope.capture_waveform(1)
    print(f"Points: {wf.preamble.points}")
    print(f"Vpp: {scope.measure_vpp():.4f} V")
```

### Auto-discover instrument

```python
from keysight_dsox1200 import list_instruments, auto_connect

instruments = list_instruments()
for addr, idn in instruments:
    print(f"{addr}: {idn}")
```

### Capture and plot

```python
import matplotlib.pyplot as plt
from keysight_dsox1200 import DSOX1200

with DSOX1200("USB0::...") as scope:
    wf = scope.capture_waveform(1)

plt.plot(wf.time * 1e3, wf.voltage)
plt.xlabel("Time (ms)")
plt.ylabel("Voltage (V)")
plt.show()
```

### Multi-channel capture

```python
with DSOX1200("USB0::...") as scope:
    waveforms = scope.capture_all_channels(channels=[1, 2])
    for ch, wf in waveforms.items():
        print(f"CH{ch}: {wf.preamble.points} points, {1/wf.preamble.x_increment/1e6:.0f} MSa/s")
```

### LAN connection via Telnet socket

The oscilloscope also accepts raw SCPI over Telnet on port 5024 (with prompt) or 5025 (without prompt):

```bash
telnet 192.168.1.10 5025
```

For programmatic access over LAN, use a standard TCPIP VISA address:

```python
scope = DSOX1200("TCPIP::192.168.1.10::inst0::INSTR")
```

---

## Launch GUI

```bash
python -m keysight_dsox1200.gui_app
# or
python examples/launch_gui.py
```

The GUI provides:
- VISA address scan and connect/disconnect
- Channel control (display, coupling, scale, offset)
- Timebase and trigger configuration
- Run / Stop / Single / Force trigger
- Multi-channel waveform capture and dark-mode plot
- Automatic measurements panel
- Screenshot capture

---

## Command Coverage

See [docs/COMMAND_COVERAGE.md](docs/COMMAND_COVERAGE.md) for the full table.

**~85 SCPI commands implemented** across: Common, Root, ACQuire, CHANnel, DISPlay, DVM,
FFT, HARDcopy, MARKer, MEASure, SAVE, RECall, SYSTem, TIMebase, TRIGger, WAVeform.

---

## Examples

| File | Description |
|------|-------------|
| `examples/basic_connection.py` | Connect, identify, query settings |
| `examples/capture_waveform.py` | Full capture, measure, CSV save, plot |
| `examples/launch_gui.py` | Launch standalone GUI |

---

## Testing

Tests require no hardware:

```bash
pip install pytest
pytest tests/
```

---

## Legal and Trademark Notice

"Keysight", "InfiniiVision", and "DSOX" are trademarks of Keysight Technologies, Inc.
This software is an independent open-source project and is not affiliated with, endorsed by,
or sponsored by Keysight Technologies, Inc.

Vendor manuals in `docs/vendor_manuals/` are excluded from version control and must not
be redistributed. They are copyrighted by Keysight Technologies, Inc.

---

## License

MIT License. See [LICENSE](LICENSE).
