# GUI Roadmap

## UI Architecture

The GUI (`gui_app.py`) is built with **tkinter** (Python stdlib) + **matplotlib** (TkAgg backend).  
It runs as a standalone desktop application — no web server, no external framework.

```
DSOX1200App (tk.Tk)
├── Toolbar           — VISA address entry, Scan, Connect, Disconnect
├── PanedWindow
│   ├── Left panel (ttk.Notebook)
│   │   ├── Channels tab
│   │   ├── Timebase tab
│   │   ├── Trigger tab
│   │   ├── Acquire tab
│   │   └── Measure tab
│   └── Right panel
│       ├── Acquisition buttons (Run / Stop / Single / Capture / Screenshot)
│       └── matplotlib figure (FigureCanvasTkAgg + NavigationToolbar2Tk)
└── StatusBar
```

---

## Front-Panel Parity Mapping

| Front-panel control | GUI equivalent | Notes |
|--------------------|----------------|-------|
| [Run/Stop] rocker key | Run / Stop buttons | Color-coded: green / red |
| [Single] key | Single button | Sets scope to single-acquisition arm |
| [Auto Scale] key | Autoscale button (Timebase tab) | Calls `:AUToscale`; 1 s wait |
| Channel 1–4 power buttons | On/Off checkboxes (Channels tab) | Per-channel enable |
| Vertical scale knob | Scale (V/div) entry (Channels tab) | Direct V/div entry |
| Vertical position knob | Offset (V) entry | Direct voltage offset |
| Coupling selector | Coupling combobox (AC / DC / GND) | — |
| Horizontal scale knob | Scale (s/div) entry (Timebase tab) | — |
| Horizontal position knob | Position (s) entry | — |
| Trigger level knob | Level (V) entry (Trigger tab) | — |
| [Force Trig] softkey | Force Trigger button | Calls `:TRIGger:FORCe` |
| [Trig 50%] softkey | Auto Level button | Calls `:TRIGger:LEVel:ASETup` |
| [Acquire] menu | Acquire tab | Mode, count, points |

**Channel colour coding** matches oscilloscope front-panel standard:
- CH1: blue (#2196F3)
- CH2: red (#F44336)
- CH3: green (#4CAF50)
- CH4: orange (#FF9800)

---

## Phase 1 — Baseline (implemented in v0.1)

- [x] VISA address entry + Scan (discovers 1200 X-Series via `list_instruments()`)
- [x] Connect / Disconnect lifecycle
- [x] Identity read on connect
- [x] Run / Stop / Single / Force trigger
- [x] Autoscale
- [x] Channel display, coupling, V/div scale, offset per CH1–4
- [x] Timebase scale and position
- [x] Edge trigger: source, slope, level, sweep, force, 50% auto-level
- [x] Acquire: type, count, points
- [x] Capture: `:DIGitize` all enabled channels → download → matplotlib plot
- [x] Automatic measurements on active channel (Measure tab)
- [x] Screenshot (`:DISPlay:DATA? PNG`)
- [x] Status bar with colour-coded feedback
- [x] Threaded capture and autoscale (non-blocking UI)

---

## Phase 2 — Planned

- [ ] Live readback: after applying settings, read back and display actual values
- [ ] Marker (cursor) panel: X1/X2 position, delta-T, delta-V readout
- [ ] DVM panel: enable, source, mode, live current value display
- [ ] Channel labels: editable label field per channel
- [ ] Probe attenuation entry (1×, 10×, 100×)
- [ ] Bandwidth limit toggle per channel
- [ ] Waveform save to CSV from GUI (file dialog)
- [ ] Setup save/recall (binary learn string, file dialog)
- [ ] Multi-channel overlay toggle in plot

---

## Phase 3 — Future

- [ ] FFT panel: enable, span, center, window, reference level
- [ ] Averaged acquisition: real-time progress indicator
- [ ] Segmented memory support
- [ ] Persist waveforms across captures (overlay mode)
- [ ] Zoom (window timebase) controls
- [ ] Error queue display in status area
- [ ] Export plot as PNG/PDF from GUI

---

## Error and Safety Behaviour

- Connection failure: shown in status bar (red) + messagebox
- Capture failure: shown in status bar only (non-blocking)
- All instrument operations in background threads — UI does not freeze
- No instrument commands issued before connection is confirmed
- Disconnect is always safe to call even if already disconnected

---

## Button State / Illumination Rules

Since this is a software GUI (not a physical front panel), button state is communicated by:
- **Run**: green background
- **Stop**: red background
- **Single**: yellow background
- **Connect/Disconnect**: enabled/disabled based on connection state
- **Status bar**: colour-coded (blue = working, green = success, red = error)
