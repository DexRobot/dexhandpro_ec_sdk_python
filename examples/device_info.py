"""Read EC board and CTRL device information.

Read-only. Firmware versions, serial numbers and temperatures are read from
the boards' object dictionary.

Run:
    python examples/device_info.py [interface]
"""

import sys
from pathlib import Path

# Allow running this file directly from the repository.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dexhand import (
    DexHandError,
    DexHandLibraryError,
    DexHandPro,
    FingerPart,
    scan_dex_interfaces,
)


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


def print_ec_info(hand):
    for info in hand.read_ec_info():
        if not info.valid:
            print("ec {:<12} invalid".format(info.module.name))
            continue

        version = hand.get_ec_firmware_version(info.module)
        print("ec {:<12} app={} sys_id=0x{:02X} sn={} temp={:.2f} C "
              "admin={} status=0x{:02X}".format(
                  info.module.name, version, info.sys_id, info.serial.text,
                  info.cur_temp / 100.0, info.admin_on, info.status))


def print_device_info(hand):
    for part in FingerPart:
        if part == FingerPart.COUNT:
            continue

        version = hand.get_ctrl_firmware_version(part)
        info = hand.read_device_info(part)
        if not info.valid:
            print("ctrl {:<20} invalid".format(part.name))
            continue

        print("ctrl {:<20} app={} sn={} temp={:.2f} C proc={:.2f} C "
              "rated: current={} rpm={} temp={}".format(
                  part.name, version, info.serial.text, info.cur_temp / 100.0,
                  info.proc_temp / 100.0, info.rated_cur, info.rated_rpm,
                  info.rated_temp))


def main(argv):
    try:
        if_name = select_interface(argv)

        hand = DexHandPro(if_name)
        try:
            hand.connect()
            print_ec_info(hand)
            print_device_info(hand)
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
