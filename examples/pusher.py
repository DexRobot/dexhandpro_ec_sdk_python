"""Move a pusher 1 mm forward, back to its start position, then disable it.

DRIVES HARDWARE: keep the hand clear before running.

Run:
    python examples/pusher.py [interface]
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
    PusherCommand,
    PusherId,
    PusherMode,
    scan_dex_interfaces,
)

PUSHER = PusherId.PUSHER0
DISTANCE_UM = 5000          # 1 mm
SPEED_UM_PER_S = 5000       # 5 mm/s


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


def print_status(hand, pusher):
    state = hand.get_pusher_status(pusher)
    print("pusher{} online={} pos={} um vel={} um/s enabled={} "
          "target_reached={} fault={} mode={}".format(
              int(pusher), state.online, state.pos, state.vel, state.enabled,
              state.target_reached, state.fault, state.mode.name))
    return state


def wait_pusher_online(hand, pusher, timeout=5.0):
    """Wait for the first pusher PDO frame after connect()."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = hand.get_pusher_status(pusher)
        if state.online:
            return state
        time.sleep(0.1)
    return hand.get_pusher_status(pusher)


def wait_at_position(hand, pusher, target_um, timeout=3.0):
    """Wait until the encoder is within 250 um of the target, like the GUI.

    The drive does not assert DS402 statusword bit 10 reliably, so arrival is
    judged from pos.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = hand.get_pusher_status(pusher)
        if abs(state.pos - target_um) <= 250:
            return True
        time.sleep(0.1)
    return False


def main(argv):
    try:
        if_name = select_interface(argv)

        hand = DexHandPro(if_name)
        try:
            hand.connect()

            print("pusher_count={}".format(hand.pusher_count))
            if hand.pusher_count == 0:
                print("no pusher found")
                return 1

            state = wait_pusher_online(hand, PUSHER)
            print_status(hand, PUSHER)
            if not state.online:
                print("pusher{} did not come online".format(int(PUSHER)))
                return 1
            if state.fault:
                print("pusher{} fault code=0x{:04X}; "
                      "call reset_pusher_fault() and retry".format(
                          int(PUSHER), state.error_code))
                return 1

            start_um = state.pos
            target_um = start_um + DISTANCE_UM

            hand.move_pusher(PUSHER, target_um, SPEED_UM_PER_S)
            reached = wait_at_position(hand, PUSHER, target_um)
            print("move_to={} um reached={}".format(target_um, reached))
            print_status(hand, PUSHER)

            hand.move_pusher(PUSHER, start_um, SPEED_UM_PER_S)
            reached = wait_at_position(hand, PUSHER, start_um)
            print("return_to={} um reached={}".format(start_um, reached))
            print_status(hand, PUSHER)
        finally:
            if hand.connected and hand.pusher_count > 0:
                hand.set_pusher_command(
                    PUSHER, PusherCommand(enable=False, mode=PusherMode.CSP))
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
