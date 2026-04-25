"""Standalone GUI for the Keysight InfiniiVision 1200 X-Series oscilloscope driver.

Launch:
    python -m keysight_dsox1200.gui_app
    python examples/launch_gui.py

Requires: tkinter (stdlib), matplotlib, numpy, pyvisa.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

from .instrument import DSOX1200
from .models import (
    AcquireType,
    ChannelCoupling,
    TimebaseMode,
    TriggerSlope,
    TriggerSource,
    TriggerSweep,
    WaveformData,
)
from .discovery import list_instruments
from .errors import DSO1200Error


_CHANNEL_COLORS = {1: "#2196F3", 2: "#F44336", 3: "#4CAF50", 4: "#FF9800"}
_COUPLING_OPTIONS = [c.value for c in ChannelCoupling]
_ACQUIRE_OPTIONS = [a.value for a in AcquireType]
_TRIGGER_SLOPE_OPTIONS = [s.value for s in TriggerSlope]
_TRIGGER_SOURCE_OPTIONS = [s.value for s in TriggerSource]
_TRIGGER_SWEEP_OPTIONS = [s.value for s in TriggerSweep]


class _StatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._label = tk.Label(self, text="Disconnected", anchor="w", relief="sunken",
                               bg="#f5f5f5", fg="#333333", padx=4)
        self._label.pack(fill="x", expand=True)

    def set(self, text: str, color: str = "#333333") -> None:
        self._label.config(text=text, fg=color)


class DSOX1200App(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Keysight InfiniiVision 1200 X-Series Control")
        self.geometry("1100x720")
        self.resizable(True, True)

        self._scope: Optional[DSOX1200] = None
        self._waveforms: dict[int, WaveformData] = {}
        self._active_channel = tk.IntVar(value=1)
        self._visa_address = tk.StringVar(value="")
        self._acq_type = tk.StringVar(value=AcquireType.NORMAL.value)
        self._acq_count = tk.IntVar(value=1)
        self._acq_points = tk.IntVar(value=1000)
        self._timebase_scale = tk.DoubleVar(value=1e-3)
        self._timebase_pos = tk.DoubleVar(value=0.0)
        self._trigger_source = tk.StringVar(value=TriggerSource.CH1.value)
        self._trigger_level = tk.DoubleVar(value=0.0)
        self._trigger_slope = tk.StringVar(value=TriggerSlope.POSITIVE.value)
        self._trigger_sweep = tk.StringVar(value=TriggerSweep.NORMAL.value)

        self._ch_enable = {i: tk.BooleanVar(value=(i == 1)) for i in range(1, 5)}
        self._ch_coupling = {i: tk.StringVar(value=ChannelCoupling.DC.value) for i in range(1, 5)}
        self._ch_scale = {i: tk.DoubleVar(value=1.0) for i in range(1, 5)}
        self._ch_offset = {i: tk.DoubleVar(value=0.0) for i in range(1, 5)}

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ---- top toolbar ----
        toolbar = tk.Frame(self, bg="#1565C0", pady=4)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="VISA address:", bg="#1565C0", fg="white").pack(side="left", padx=(8, 2))
        addr_entry = tk.Entry(toolbar, textvariable=self._visa_address, width=42)
        addr_entry.pack(side="left", padx=2)

        tk.Button(toolbar, text="Scan", command=self._scan_instruments,
                  bg="#90CAF9", relief="flat").pack(side="left", padx=2)
        self._btn_connect = tk.Button(toolbar, text="Connect", command=self._connect,
                                      bg="#A5D6A7", relief="flat")
        self._btn_connect.pack(side="left", padx=2)
        self._btn_disconnect = tk.Button(toolbar, text="Disconnect", command=self._disconnect,
                                         bg="#EF9A9A", relief="flat", state="disabled")
        self._btn_disconnect.pack(side="left", padx=2)

        # ---- main panes ----
        paned = tk.PanedWindow(self, orient="horizontal", sashrelief="raised")
        paned.pack(fill="both", expand=True)

        left = tk.Frame(paned, width=280)
        paned.add(left, minsize=260)

        right = tk.Frame(paned)
        paned.add(right, minsize=600)

        self._build_left_panel(left)
        self._build_plot_panel(right)

        # ---- status bar ----
        self._status = _StatusBar(self)
        self._status.pack(fill="x", side="bottom")

    def _build_left_panel(self, parent):
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        ch_frame = ttk.Frame(nb)
        nb.add(ch_frame, text="Channels")
        self._build_channel_tab(ch_frame)

        tb_frame = ttk.Frame(nb)
        nb.add(tb_frame, text="Timebase")
        self._build_timebase_tab(tb_frame)

        trig_frame = ttk.Frame(nb)
        nb.add(trig_frame, text="Trigger")
        self._build_trigger_tab(trig_frame)

        acq_frame = ttk.Frame(nb)
        nb.add(acq_frame, text="Acquire")
        self._build_acquire_tab(acq_frame)

        meas_frame = ttk.Frame(nb)
        nb.add(meas_frame, text="Measure")
        self._build_measure_tab(meas_frame)

    def _build_channel_tab(self, parent):
        ch_sel = tk.Frame(parent)
        ch_sel.pack(fill="x", padx=4, pady=4)
        tk.Label(ch_sel, text="Active channel:").pack(side="left")
        for i in range(1, 5):
            tk.Radiobutton(ch_sel, text=str(i), variable=self._active_channel,
                           value=i, fg=_CHANNEL_COLORS[i]).pack(side="left")

        for ch in range(1, 5):
            grp = ttk.LabelFrame(parent, text=f"CH{ch}")
            grp.pack(fill="x", padx=4, pady=2)

            row0 = tk.Frame(grp)
            row0.pack(fill="x")
            tk.Checkbutton(row0, text="On", variable=self._ch_enable[ch]).pack(side="left")
            tk.Label(row0, text="Coup:").pack(side="left")
            ttk.Combobox(row0, textvariable=self._ch_coupling[ch],
                         values=_COUPLING_OPTIONS, width=5, state="readonly").pack(side="left")

            row1 = tk.Frame(grp)
            row1.pack(fill="x")
            tk.Label(row1, text="Scale (V/div):").pack(side="left")
            tk.Entry(row1, textvariable=self._ch_scale[ch], width=8).pack(side="left")

            row2 = tk.Frame(grp)
            row2.pack(fill="x")
            tk.Label(row2, text="Offset (V):").pack(side="left")
            tk.Entry(row2, textvariable=self._ch_offset[ch], width=8).pack(side="left")

        tk.Button(parent, text="Apply Channels", command=self._apply_channels,
                  bg="#BBDEFB").pack(pady=4)

    def _build_timebase_tab(self, parent):
        rows = [
            ("Scale (s/div):", self._timebase_scale),
            ("Position (s):", self._timebase_pos),
        ]
        for label, var in rows:
            row = tk.Frame(parent)
            row.pack(fill="x", padx=4, pady=2)
            tk.Label(row, text=label, width=16, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, width=12).pack(side="left")

        tk.Button(parent, text="Apply Timebase", command=self._apply_timebase,
                  bg="#BBDEFB").pack(pady=4)
        tk.Button(parent, text="Autoscale", command=self._autoscale,
                  bg="#C8E6C9").pack(pady=2)

    def _build_trigger_tab(self, parent):
        rows = [
            ("Source:", self._trigger_source, _TRIGGER_SOURCE_OPTIONS),
            ("Slope:", self._trigger_slope, _TRIGGER_SLOPE_OPTIONS),
            ("Sweep:", self._trigger_sweep, _TRIGGER_SWEEP_OPTIONS),
        ]
        for label, var, opts in rows:
            row = tk.Frame(parent)
            row.pack(fill="x", padx=4, pady=2)
            tk.Label(row, text=label, width=10, anchor="w").pack(side="left")
            ttk.Combobox(row, textvariable=var, values=opts, width=12,
                         state="readonly").pack(side="left")

        row = tk.Frame(parent)
        row.pack(fill="x", padx=4, pady=2)
        tk.Label(row, text="Level (V):", width=10, anchor="w").pack(side="left")
        tk.Entry(row, textvariable=self._trigger_level, width=10).pack(side="left")

        tk.Button(parent, text="Apply Trigger", command=self._apply_trigger,
                  bg="#BBDEFB").pack(pady=4)
        tk.Button(parent, text="Force Trigger", command=self._force_trigger,
                  bg="#FFE0B2").pack(pady=2)
        tk.Button(parent, text="Auto Level (50%)", command=self._auto_level,
                  bg="#F3E5F5").pack(pady=2)

    def _build_acquire_tab(self, parent):
        row = tk.Frame(parent)
        row.pack(fill="x", padx=4, pady=2)
        tk.Label(row, text="Mode:", width=10, anchor="w").pack(side="left")
        ttk.Combobox(row, textvariable=self._acq_type, values=_ACQUIRE_OPTIONS,
                     width=12, state="readonly").pack(side="left")

        row2 = tk.Frame(parent)
        row2.pack(fill="x", padx=4, pady=2)
        tk.Label(row2, text="Averages:", width=10, anchor="w").pack(side="left")
        tk.Entry(row2, textvariable=self._acq_count, width=8).pack(side="left")

        row3 = tk.Frame(parent)
        row3.pack(fill="x", padx=4, pady=2)
        tk.Label(row3, text="Points:", width=10, anchor="w").pack(side="left")
        tk.Entry(row3, textvariable=self._acq_points, width=8).pack(side="left")

        tk.Button(parent, text="Apply Acquire", command=self._apply_acquire,
                  bg="#BBDEFB").pack(pady=4)

    def _build_measure_tab(self, parent):
        self._measure_text = tk.Text(parent, height=14, state="disabled",
                                     font=("Courier", 9), bg="#FAFAFA")
        self._measure_text.pack(fill="both", expand=True, padx=4, pady=4)
        tk.Button(parent, text="Measure Active Channel", command=self._run_measurements,
                  bg="#C8E6C9").pack(pady=4)
        tk.Button(parent, text="Clear", command=self._clear_measurements,
                  bg="#FFCDD2").pack(pady=2)

    def _build_plot_panel(self, parent):
        btn_row = tk.Frame(parent)
        btn_row.pack(fill="x", padx=4, pady=4)

        self._btn_run = tk.Button(btn_row, text="Run", command=self._run_scope,
                                  bg="#A5D6A7", width=8)
        self._btn_run.pack(side="left", padx=2)
        self._btn_stop = tk.Button(btn_row, text="Stop", command=self._stop_scope,
                                   bg="#EF9A9A", width=8)
        self._btn_stop.pack(side="left", padx=2)
        self._btn_single = tk.Button(btn_row, text="Single", command=self._single_scope,
                                     bg="#FFF9C4", width=8)
        self._btn_single.pack(side="left", padx=2)
        self._btn_capture = tk.Button(btn_row, text="Capture", command=self._capture,
                                      bg="#BBDEFB", width=8)
        self._btn_capture.pack(side="left", padx=2)
        self._btn_screenshot = tk.Button(btn_row, text="Screenshot", command=self._screenshot,
                                          bg="#E1BEE7", width=10)
        self._btn_screenshot.pack(side="left", padx=2)

        fig = Figure(figsize=(8, 5), dpi=100, facecolor="#1a1a1a")
        self._ax = fig.add_subplot(111, facecolor="#111111")
        self._ax.set_xlabel("Time (s)", color="white")
        self._ax.set_ylabel("Voltage (V)", color="white")
        self._ax.tick_params(colors="white")
        for spine in self._ax.spines.values():
            spine.set_edgecolor("#555555")
        self._ax.grid(True, color="#333333", linestyle="--", linewidth=0.5)
        self._canvas = FigureCanvasTkAgg(fig, master=parent)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)
        self._fig = fig

        toolbar = NavigationToolbar2Tk(self._canvas, parent)
        toolbar.update()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _scan_instruments(self):
        self._status.set("Scanning for instruments…", "#1565C0")
        self.update()
        try:
            found = list_instruments()
        except ImportError as e:
            messagebox.showerror("Missing dependency", str(e))
            return
        if not found:
            self._status.set("No InfiniiVision 1200 X-Series instruments found.", "#B71C1C")
            return
        addr, idn = found[0]
        self._visa_address.set(addr)
        self._status.set(f"Found: {idn}", "#1B5E20")

    def _connect(self):
        addr = self._visa_address.get().strip()
        if not addr:
            messagebox.showwarning("No address", "Enter a VISA address or use Scan.")
            return
        self._status.set(f"Connecting to {addr}…", "#1565C0")
        self.update()
        try:
            self._scope = DSOX1200(addr)
            idn = self._scope.identify()
        except Exception as e:
            self._scope = None
            self._status.set(f"Connection failed: {e}", "#B71C1C")
            messagebox.showerror("Connection error", str(e))
            return
        self._btn_connect.config(state="disabled")
        self._btn_disconnect.config(state="normal")
        self._status.set(f"Connected: {idn}", "#1B5E20")

    def _disconnect(self):
        if self._scope:
            self._scope.close()
            self._scope = None
        self._btn_connect.config(state="normal")
        self._btn_disconnect.config(state="disabled")
        self._status.set("Disconnected", "#333333")

    def _on_close(self):
        self._disconnect()
        self.destroy()

    # ------------------------------------------------------------------
    # Instrument control callbacks
    # ------------------------------------------------------------------

    def _require_scope(self) -> bool:
        if self._scope is None:
            messagebox.showwarning("Not connected", "Connect to an instrument first.")
            return False
        return True

    def _run_in_thread(self, fn, *args):
        t = threading.Thread(target=fn, args=args, daemon=True)
        t.start()

    def _apply_channels(self):
        if not self._require_scope():
            return
        try:
            for ch in range(1, 5):
                self._scope.channel_display(ch, self._ch_enable[ch].get())
                self._scope.channel_coupling(ch, ChannelCoupling(self._ch_coupling[ch].get()))
                self._scope.channel_scale(ch, self._ch_scale[ch].get())
                self._scope.channel_offset(ch, self._ch_offset[ch].get())
            self._status.set("Channels applied.", "#1B5E20")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _apply_timebase(self):
        if not self._require_scope():
            return
        try:
            self._scope.timebase_scale(self._timebase_scale.get())
            self._scope.timebase_position(self._timebase_pos.get())
            self._status.set("Timebase applied.", "#1B5E20")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _apply_trigger(self):
        if not self._require_scope():
            return
        try:
            from .models import TriggerSource, TriggerSlope, TriggerSweep
            self._scope.configure_trigger_edge(
                source=TriggerSource(self._trigger_source.get()),
                level_v=self._trigger_level.get(),
                slope=TriggerSlope(self._trigger_slope.get()),
                sweep=TriggerSweep(self._trigger_sweep.get()),
            )
            self._status.set("Trigger applied.", "#1B5E20")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _apply_acquire(self):
        if not self._require_scope():
            return
        try:
            self._scope.configure_acquire(
                acq_type=AcquireType(self._acq_type.get()),
                count=self._acq_count.get(),
                points=self._acq_points.get(),
            )
            self._status.set("Acquire settings applied.", "#1B5E20")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _autoscale(self):
        if not self._require_scope():
            return
        self._status.set("Autoscaling…", "#1565C0")
        self._run_in_thread(self._do_autoscale)

    def _do_autoscale(self):
        try:
            self._scope.autoscale()
            self.after(0, lambda: self._status.set("Autoscale complete.", "#1B5E20"))
        except Exception as e:
            self.after(0, lambda: self._status.set(f"Error: {e}", "#B71C1C"))

    def _force_trigger(self):
        if not self._require_scope():
            return
        try:
            self._scope.trigger_force()
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _auto_level(self):
        if not self._require_scope():
            return
        try:
            self._scope.trigger_level_asetup()
            self._status.set("Trigger level set to 50%.", "#1B5E20")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _run_scope(self):
        if not self._require_scope():
            return
        try:
            self._scope.run()
            self._status.set("Running.", "#1B5E20")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _stop_scope(self):
        if not self._require_scope():
            return
        try:
            self._scope.stop()
            self._status.set("Stopped.", "#E65100")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _single_scope(self):
        if not self._require_scope():
            return
        try:
            self._scope.single()
            self._status.set("Armed — waiting for trigger.", "#1565C0")
        except Exception as e:
            self._status.set(f"Error: {e}", "#B71C1C")

    def _capture(self):
        if not self._require_scope():
            return
        self._status.set("Capturing…", "#1565C0")
        self._run_in_thread(self._do_capture)

    def _do_capture(self):
        try:
            channels = [ch for ch in range(1, 5) if self._ch_enable[ch].get()]
            if not channels:
                channels = [self._active_channel.get()]
            waveforms = self._scope.capture_all_channels(channels=channels)
            self.after(0, lambda: self._update_plot(waveforms))
        except Exception as e:
            self.after(0, lambda: self._status.set(f"Capture error: {e}", "#B71C1C"))

    def _update_plot(self, waveforms: dict):
        self._waveforms = waveforms
        self._ax.cla()
        self._ax.set_facecolor("#111111")
        self._ax.set_xlabel("Time (s)", color="white")
        self._ax.set_ylabel("Voltage (V)", color="white")
        self._ax.tick_params(colors="white")
        for spine in self._ax.spines.values():
            spine.set_edgecolor("#555555")
        self._ax.grid(True, color="#333333", linestyle="--", linewidth=0.5)

        for ch, wf in waveforms.items():
            self._ax.plot(wf.time, wf.voltage, color=_CHANNEL_COLORS[ch],
                          linewidth=0.8, label=f"CH{ch}")
        self._ax.legend(facecolor="#222222", labelcolor="white")
        self._canvas.draw()
        self._status.set(
            f"Captured {len(waveforms)} channel(s), "
            f"{next(iter(waveforms.values())).preamble.points} points each.",
            "#1B5E20"
        )

    def _screenshot(self):
        if not self._require_scope():
            return
        try:
            data = self._scope.screenshot("screenshot.png")
            self._status.set(f"Screenshot saved: screenshot.png ({len(data)} bytes).", "#1B5E20")
        except Exception as e:
            self._status.set(f"Screenshot error: {e}", "#B71C1C")

    def _run_measurements(self):
        if not self._require_scope():
            return
        from .models import MeasureSource
        ch = self._active_channel.get()
        src = MeasureSource(f"CHANnel{ch}")
        lines = [f"--- CH{ch} Measurements ---"]
        pairs = [
            ("Frequency",    self._scope.measure_frequency),
            ("Period",       self._scope.measure_period),
            ("Duty Cycle",   self._scope.measure_duty_cycle),
            ("Vmax",         self._scope.measure_vmax),
            ("Vmin",         self._scope.measure_vmin),
            ("Vpp",          self._scope.measure_vpp),
            ("Vrms",         self._scope.measure_vrms),
            ("Vavg",         self._scope.measure_vaverage),
            ("Rise time",    self._scope.measure_risetime),
            ("Fall time",    self._scope.measure_falltime),
        ]
        for name, fn in pairs:
            try:
                val = fn(src)
                lines.append(f"{name:12s}: {val:.6g}")
            except Exception:
                lines.append(f"{name:12s}: ---")
        text = "\n".join(lines)
        self._measure_text.config(state="normal")
        self._measure_text.insert("end", text + "\n\n")
        self._measure_text.config(state="disabled")
        self._measure_text.see("end")

    def _clear_measurements(self):
        self._measure_text.config(state="normal")
        self._measure_text.delete("1.0", "end")
        self._measure_text.config(state="disabled")


def main():
    app = DSOX1200App()
    app.mainloop()


if __name__ == "__main__":
    main()
