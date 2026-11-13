"""Print hand information and poll joint angles.

Read-only. Joint angles come from the latest PDO snapshot, so this example
does not send anything to the hand.

Run:
    python examples/status_poll.py [interface]
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
    JointId,
    scan_dex_interfaces,
    version_info,
)

# Joints grouped by finger, in the order they are printed.
FINGERS = [
    ("thumb", [("dist", JointId.THUMB_DIST),
               ("midd", JointId.THUMB_MIDD),
               ("swng", JointId.THUMB_PROX_SWNG),
               ("flex", JointId.THUMB_PROX_FLEX)]),
    ("index", [("swng", JointId.INDEX_PROX_SWNG),
               ("flex", JointId.INDEX_PROX_FLEX),
               ("dist", JointId.INDEX_DIST_COUPLED)]),
    ("middle", [("swng", JointId.MIDDLE_PROX_SWNG),
                ("flex", JointId.MIDDLE_PROX_FLEX),
                ("dist", JointId.MIDDLE_DIST_COUPLED)]),
    ("ring", [("swng", JointId.RING_PROX_SWNG),
              ("flex", JointId.RING_PROX_FLEX),
              ("dist", JointId.RING_DIST_COUPLED)]),
    ("little", [("swng", JointId.LITTLE_PROX_SWNG),
                ("flex", JointId.LITTLE_PROX_FLEX),
                ("dist", JointId.LITTLE_DIST_COUPLED)]),
]


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


def print_hand_info(hand):
    info = hand.get_hand_info()
    print("side={} modules={} pushers={}".format(
        info.side.name, info.module_count, info.pusher_count))

    for module in info.modules:
        print("  module {} version={} op={}".format(
            module.module.name, module.version.name, module.op))

        version = hand.get_ec_firmware_version(module.module)
        print("  ec {} app={}".format(module.module.name, version))

    diagnostics = hand.get_diagnostics()
    print("pdo_healthy={} wkc={}/{}".format(
        diagnostics.pdo_healthy,
        diagnostics.last_wkc,
        diagnostics.expected_wkc))


def wait_status(hand, timeout=5.0):
    """Wait for the first PDO status snapshot."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = hand.get_hand_status()
        if status is not None:
            return status
        time.sleep(0.1)
    return None


def print_status(status, elapsed):
    print("[{:4.1f}s] side={}".format(elapsed, status.side.name))
    for finger, joints in FINGERS:
        values = "  ".join(
            "{}={:7.2f}".format(label, status.joints[joint].angle / 100.0)
            for label, joint in joints)
        print("  {:<7} {}".format(finger, values))


def main(argv):
    try:
        if_name = select_interface(argv)
        print(version_info())
        print("adapter:", if_name)

        hand = DexHandPro(if_name)
        try:
            hand.connect()
            print_hand_info(hand)

            if wait_status(hand) is None:
                print("no status snapshot received")
                return 1

            start = time.time()
            for _ in range(6):
                status = hand.get_hand_status()
                if status is not None:
                    print_status(status, time.time() - start)
                time.sleep(0.5)
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
