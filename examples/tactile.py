"""Poll all tactile regions and print the first frame of each.

Read-only. Tactile frames rotate through the PDO, so it takes a few seconds
before every region has been seen.

Run:
    python examples/tactile.py [interface]
"""

import sys
import time
from pathlib import Path

# Allow running this file directly from the repository.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dexhand import (
    DexHandError,
    DexHandLibraryError,
    DexHandPro,
    TactilePart,
    scan_dex_interfaces,
)

POLL_SECONDS = 10.0


def select_interface(argv):
    """Use the command-line interface name, or the only one with slaves."""
    if argv:
        return argv[0]

    candidates = scan_dex_interfaces()
    if not candidates:
        raise SystemExit("no interface with EtherCAT slaves found; "
                         "run examples/scan.py")

    if len(candidates) > 1:
        print("interfaces with EtherCAT slaves:")
        for info in candidates:
            print("  {}  {}".format(info.name, info.description))
        print("using {}; pass another name to choose".format(candidates[0].name))

    return candidates[0].name


def main(argv):
    try:
        if_name = select_interface(argv)

        hand = DexHandPro(if_name)
        try:
            hand.connect()

            seen = set()
            deadline = time.time() + POLL_SECONDS

            while time.time() < deadline:
                for part in TactilePart:
                    if part == TactilePart.COUNT or part in seen:
                        continue

                    data = hand.get_tactile(part)
                    if data is None:
                        continue

                    seen.add(part)
                    peak = max(data.values) if data.values else 0
                    print("{:<20} count={:2d} max={}".format(
                        part.name, data.count, peak))

                time.sleep(0.1)

            print("regions received: {}/{}".format(
                len(seen), int(TactilePart.COUNT)))
            if not seen:
                print("no tactile frame received")
                return 1
        finally:
            hand.disconnect()
            hand.close()
    except DexHandLibraryError as exc:
        print("native library:", exc)
        return 1
    except DexHandError as exc:
        print("sdk error:", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
