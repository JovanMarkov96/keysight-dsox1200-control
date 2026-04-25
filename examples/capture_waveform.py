"""Example: capture a waveform from channel 1 and plot it with matplotlib.

Usage:
    python examples/capture_waveform.py
    python examples/capture_waveform.py "USB0::0x2A8D::0x1797::MYSERIAL::0::INSTR"

Saves waveform data to waveform_ch1.csv in the current directory.
"""

import sys
import csv
import numpy as np

from keysight_dsox1200 import (
    DSOX1200,
    AcquireType,
    ChannelCoupling,
    TimebaseMode,
    TriggerSource,
    TriggerSlope,
    TriggerSweep,
    list_instruments,
)


def main(visa_address: str = None):
    if visa_address is None:
        found = list_instruments()
        if not found:
            print("No instrument found.")
            sys.exit(1)
        visa_address = found[0][0]
        print(f"Using: {visa_address}")

    with DSOX1200(visa_address, timeout_ms=15_000) as scope:
        print("Connected:", scope.identify())

        # --- Reset to known state ---
        scope.reset()
        scope.clear_status()

        # --- Configure channel 1 ---
        scope.configure_channel(
            1,
            display=True,
            coupling=ChannelCoupling.DC,
            probe=1.0,          # 1:1 probe
            scale_v=0.5,        # 500 mV/div → 4 V full scale
            offset_v=0.0,
        )

        # --- Configure timebase: 1 ms/div → 10 ms full scale ---
        scope.configure_timebase(
            mode=TimebaseMode.MAIN,
            scale_s=1e-3,
            position_s=0.0,
        )

        # --- Configure edge trigger on CH1 ---
        scope.configure_trigger_edge(
            source=TriggerSource.CH1,
            level_v=0.0,
            slope=TriggerSlope.POSITIVE,
            sweep=TriggerSweep.AUTO,
        )

        # --- Configure acquisition: normal, 1000 points ---
        scope.configure_acquire(
            acq_type=AcquireType.NORMAL,
            points=1000,
        )

        # --- Capture waveform (digitize + download) ---
        print("Capturing waveform…")
        wf = scope.capture_waveform(channel=1, digitize=True)

        print(f"Points:      {wf.preamble.points}")
        print(f"X increment: {wf.preamble.x_increment*1e9:.2f} ns/point")
        print(f"Sample rate: {1/wf.preamble.x_increment/1e6:.1f} MSa/s")
        print(f"Time span:   {(wf.time[-1]-wf.time[0])*1e3:.3f} ms")

        # --- Automatic measurements ---
        from keysight_dsox1200 import MeasureSource
        src = MeasureSource.CH1
        print(f"\nFrequency:  {scope.measure_frequency(src):.4f} Hz")
        print(f"Vpp:        {scope.measure_vpp(src):.4f} V")
        print(f"Vrms:       {scope.measure_vrms(src):.4f} V")
        print(f"Vmax:       {scope.measure_vmax(src):.4f} V")
        print(f"Vmin:       {scope.measure_vmin(src):.4f} V")

        # --- Save to CSV ---
        csv_path = "waveform_ch1.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "voltage_V"])
            for t, v in zip(wf.time, wf.voltage):
                writer.writerow([f"{t:.12g}", f"{v:.8g}"])
        print(f"\nSaved {len(wf.time)} points to {csv_path}")

        # --- Plot ---
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(wf.time * 1e3, wf.voltage, color="#2196F3", linewidth=0.8)
            ax.set_xlabel("Time (ms)")
            ax.set_ylabel("Voltage (V)")
            ax.set_title("CH1 Waveform — Keysight DSOX1200")
            ax.grid(True, linestyle="--", alpha=0.4)
            plt.tight_layout()
            plt.savefig("waveform_ch1.png", dpi=150)
            plt.show()
            print("Plot saved to waveform_ch1.png")
        except ImportError:
            print("matplotlib not available — skipping plot.")


if __name__ == "__main__":
    addr = sys.argv[1] if len(sys.argv) > 1 else None
    main(addr)
