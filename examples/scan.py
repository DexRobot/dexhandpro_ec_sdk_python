"""List network interfaces and mark those with EtherCAT slaves.

Read-only. Run this first to find the interface name used by the other
examples.

Run:
    python examples/scan.py
"""

import sys
from pathlib import Path

# Allow running this file directly from the repository.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dexhand import DexHandLibraryError, scan_dex_interfaces, scan_interfaces


def main():
    try:
        interfaces = scan_interfaces()
        with_slaves = {info.name for info in scan_dex_interfaces()}
    except DexHandLibraryError as exc:
        print("native library:", exc)
        return 1

    if not interfaces:
        print("no network interface found")
        print("check: NIC access (Npcap installed on Windows / root or "
              "CAP_NET_RAW on Linux)")
        return 1

    print("{:<52} {:<46} {}".format("interface", "description", "EtherCAT"))
    for info in interfaces:
        print("{:<52} {:<46} {}".format(
            info.name,
            info.description,
            "yes" if info.name in with_slaves else "-"))

    if not with_slaves:
        print()
        print("no interface with EtherCAT slaves found")
        print("check: hand powered, cable connected, NIC access "
              "(Npcap on Windows / root or CAP_NET_RAW on Linux)")
        return 1

    print()
    print("run: python examples/status_poll.py <interface>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
