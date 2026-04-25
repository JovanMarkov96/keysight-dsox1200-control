"""Example: connect to the oscilloscope, print identity, and query state.

Usage:
    python examples/basic_connection.py
    python examples/basic_connection.py "USB0::0x2A8D::0x1797::MYSERIAL::0::INSTR"
    python examples/basic_connection.py "TCPIP::192.168.1.10::inst0::INSTR"
"""

import sys
from keysight_dsox1200 import DSOX1200, list_instruments

def main(visa_address: str = None):
    # Auto-discover if no address given
    if visa_address is None:
        print("Scanning for InfiniiVision 1200 X-Series instruments…")
        found = list_instruments()
        if not found:
            print("No instruments found. Connect via USB or LAN and retry.")
            sys.exit(1)
        visa_address, idn = found[0]
        print(f"Found: {idn}")
        print(f"Address: {visa_address}\n")

    with DSOX1200(visa_address) as scope:
        print("Identity:", scope.identify())
        print("Options: ", scope.get_options())
        print("Date:    ", scope.system_date_query())
        print("Time:    ", scope.system_time_query())

        # Check for errors
        code, msg = scope.system_error_query()
        if code != 0:
            print(f"Instrument error {code}: {msg}")
        else:
            print("Error queue: clear")

        # Read current timebase
        tb_scale = scope.timebase_scale_query()
        tb_pos   = scope.timebase_position_query()
        print(f"\nTimebase: {tb_scale*1e3:.3f} ms/div, position {tb_pos*1e6:.1f} µs")

        # Read channel 1 settings
        ch_scale  = scope.channel_scale_query(1)
        ch_offset = scope.channel_offset_query(1)
        ch_coup   = scope.channel_coupling_query(1)
        print(f"CH1: {ch_scale:.3f} V/div, offset {ch_offset:.3f} V, coupling {ch_coup}")

        # Sample rate
        srate = scope.acquire_srate_query()
        print(f"Sample rate: {srate/1e6:.0f} MSa/s")

    print("\nDone.")


if __name__ == "__main__":
    addr = sys.argv[1] if len(sys.argv) > 1 else None
    main(addr)
