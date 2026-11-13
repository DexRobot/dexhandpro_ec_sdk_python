"""Move one joint by +10 degrees and read it back.

DRIVES HARDWARE: keep the hand clear before running.

Run:
    python examples/move_joint.py [interface]
"""

import sys
import time
from pathlib import Path

# Allow running this file directly from the repository.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dexhand import (
    ControlMode,
    DexHandError,
    DexHandLibraryError,
    DexHandPro,
    JointId,
    JointTarget,
    scan_dex_interfaces,
)

JOINT = JointId.INDEX_DIST_COUPLED
DELTA_DEG = 10.0


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


def wait_status(hand, timeout=5.0):
    """Wait for the first PDO status snapshot."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = hand.get_hand_status()
        if status is not None:
            return status
        time.sleep(0.1)
    return None


def main(argv):
    try:
        if_name = select_interface(argv)

        hand = DexHandPro(if_name)
        try:
            hand.connect()

            status = wait_status(hand)
            if status is None:
                print("no status snapshot received")
                return 1

            state = status.joints[JOINT]
            if not state.online:
                print("joint {} is not online".format(JOINT.name))
                return 1

            current_deg = state.angle / 100.0
            target_deg = current_deg + DELTA_DEG
            print("joint={} current={:.2f} deg target={:.2f} deg".format(
                JOINT.name, current_deg, target_deg))

            hand.set_control_mode(ControlMode.JOINT_POS)

            # Same parameters as the C++ UnitTest motion check.
            hand.move_joint(JOINT, JointTarget(
                target_deg=target_deg,
                speed_rpm=10000,
                current_ma=70,
                kp=464,
                kd=0,
                enable=True))

            time.sleep(3.0)

            status = hand.get_hand_status()
            if status is not None:
                state = status.joints[JOINT]
                print("readback angle={:.2f} deg current={} mA velocity={} rpm".format(
                    state.angle / 100.0, state.current, state.velocity))

            diagnostics = hand.get_diagnostics()
            print("pdo_healthy={} wkc={}/{}".format(
                diagnostics.pdo_healthy,
                diagnostics.last_wkc,
                diagnostics.expected_wkc))

            hand.emergency_stop()
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
