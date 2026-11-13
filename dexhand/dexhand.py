"""
dexhand.dexhand - high-level ctypes wrapper.

Public API: from dexhand import DexHandPro, ...
"""

from __future__ import annotations

import ctypes
from typing import Callable, List, Optional

from ._capi import (
    DexHandLibraryError,
    _DeviceInfo,
    _Diagnostics,
    _EcInfo,
    _ErrorCallback,
    _ErrorInfo,
    _FirmwareVersion,
    _HandCommand,
    _HandInfo,
    _InterfaceInfo,
    _JointState,
    _JointTarget,
    _MAX_JOINTS,
    _PusherCommand,
    _PusherState,
    _StatusCallback,
    _StatusSnapshot,
    _TactileData,
    _get_lib,
)
from ._types import (
    AdapterType,
    ConnectStage,
    ControlMode,
    DexHandError,
    DeviceInfo,
    Diagnostics,
    EcInfo,
    ErrorInfo,
    FaultDomain,
    FingerPart,
    FirmwareVersion,
    HandCommand,
    HandInfo,
    HandModule,
    HandSide,
    InterfaceInfo,
    JointId,
    JointState,
    JointTarget,
    ModuleInfo,
    PdoVersion,
    ProductType,
    PusherCommand,
    PusherField,
    PusherId,
    PusherInfo,
    PusherMode,
    PusherState,
    SerialNumber,
    StatusSnapshot,
    SysErrorCode,
    TactileData,
    TactilePart,
    _decode_cstr,
    _device_info_from_c,
    _ec_info_from_c,
    _error_from_c,
    _firmware_from_c,
    _index,
    _int_in,
    _pusher_command_from_c,
    _pusher_state_from_c,
    _status_from_c,
    _tactile_from_c,
)


__version__ = "1.0.1"


def native_version() -> str:
    """Native library version, for example "1.0.2"."""
    return _get_lib().dexhand_sdk_version().decode("utf-8", "replace")


def native_abi_version() -> int:
    """C ABI version implemented by the native library."""
    return int(_get_lib().dexhand_c_abi_version())


def version_info() -> str:
    """Formatted Python/native/ABI versions for logs and support."""
    return "python={} native={} abi={}".format(
        __version__, native_version(), native_abi_version())


def scan_interfaces(adapter: AdapterType = AdapterType.EC_SOEM,
                    only_with_slaves: bool = False) -> List[InterfaceInfo]:
    """List network interfaces; only_with_slaves keeps interfaces with slaves."""
    lib = _get_lib()
    flag = 1 if only_with_slaves else 0

    total = int(lib.dexhand_scan_interfaces(int(adapter), None, 0, flag))
    if total < 0:
        raise DexHandError(SysErrorCode.INTERNAL, "interface scan failed")
    if total == 0:
        return []

    buffer = (_InterfaceInfo * total)()
    written = int(lib.dexhand_scan_interfaces(int(adapter), buffer, total, flag))
    if written < 0:
        raise DexHandError(SysErrorCode.INTERNAL, "interface scan failed")

    result = []
    for i in range(min(written, total)):
        result.append(InterfaceInfo(
            name=_decode_cstr(buffer[i].name),
            description=_decode_cstr(buffer[i].description)))
    return result


def scan_dex_interfaces(adapter: AdapterType = AdapterType.EC_SOEM) -> List[InterfaceInfo]:
    """List interfaces that currently have EtherCAT slaves attached."""
    return scan_interfaces(adapter, only_with_slaves=True)


# ============================================================================
# high-level wrapper
# ============================================================================

class DexHandPro:
    """DexHand Pro instance.

    Creation and connection are explicit:

        interfaces = scan_dex_interfaces()
        for info in interfaces:
            print(info.name, info.description)

        hand = DexHandPro(interfaces[0].name)
        hand.connect()

        control and setting...

        hand.disconnect()
        hand.close()

    The context manager only guarantees close(); call connect() explicitly.
    Methods raise DexHandError on failure.
    """

    def __init__(self, if_name: str, adapter: AdapterType = AdapterType.EC_SOEM):
        """Bind a hand instance to one EtherCAT interface.

        if_name comes from scan_interfaces() or scan_dex_interfaces(). The
        instance is not connected until connect() succeeds.
        """
        if not if_name:
            raise ValueError("if_name is required; call scan_interfaces() to list candidates")

        self._lib = _get_lib()
        self._handle = None
        self._user_status_cb = None
        self._user_error_cb = None
        self._status_cb = None
        self._error_cb = None

        self._if_name = if_name
        handle = self._lib.dexhand_create(int(adapter), if_name.encode("utf-8"))
        if not handle:
            raise DexHandError(SysErrorCode.INTERNAL, "dexhand_create failed")
        self._handle = handle

    # -- lifecycle ---------------------------------------------------------

    @property
    def if_name(self) -> str:
        """EtherCAT interface name this instance is bound to."""
        return self._if_name

    @property
    def connected(self) -> bool:
        """True while a control session is connect."""
        return bool(self._lib.dexhand_is_connected(self._handle)) if self._handle else False

    @property
    def available(self) -> bool:
        """True while the native adapter is open."""
        return bool(self._lib.dexhand_is_available(self._handle)) if self._handle else False

    @property
    def listening(self) -> bool:
        """True while status callbacks are enabled."""
        return bool(self._lib.dexhand_is_listening(self._handle)) if self._handle else False

    @property
    def product_type(self) -> ProductType:
        """Product type of this instance; UNSUPPORTED after close()."""
        if not self._handle:
            return ProductType.UNSUPPORTED
        return ProductType(int(self._lib.dexhand_product_type(self._handle)))

    def connect(self, listen: bool = True) -> "DexHandPro":
        """connect current hand instance: Open the interface, map PDOs and enter OPERATIONAL.

        listen=False keeps PDO running but suppresses status callbacks; use
        listen() to toggle them later. Blocks while the bus is configured, so
        do not call it from a callback. Returns self for chaining.
        """
        self._require()
        self._check(self._lib.dexhand_connect(self._handle, 1 if listen else 0), "connect")
        return self

    def disconnect(self) -> None:
        """disconnect current hand instance and leave the motors in a safe state."""
        if self._handle:
            self._check(self._lib.dexhand_disconnect(self._handle), "disconnect")

    def close(self) -> None:
        """Release the native instance. Safe to call more than once.

        Undisconnected sessions are disconnected automatically.
        """
        if self._handle is None:
            return

        handle = self._handle
        self._handle = None
        try:
            self._lib.dexhand_set_status_callback(handle, None, None)
            self._lib.dexhand_set_error_callback(handle, None, None)
            self._lib.dexhand_destroy(handle)
        finally:
            self._status_cb = None
            self._error_cb = None
            self._user_status_cb = None
            self._user_error_cb = None

    def __enter__(self) -> "DexHandPro":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # -- errors ------------------------------------------------------------

    def _require(self) -> None:
        if self._handle is None:
            raise DexHandError(SysErrorCode.NONE, "instance is closed")

    def _read_error(self):
        code = int(self._lib.dexhand_error_code(self._handle))
        buffer = ctypes.create_string_buffer(1024)
        length = int(self._lib.dexhand_error_message(self._handle, buffer, len(buffer)))
        message = _decode_cstr(buffer.raw[:max(0, length)]) if length > 0 else ""
        try:
            error_code = SysErrorCode(code)
        except ValueError:
            error_code = SysErrorCode.INTERNAL
        return error_code, message

    def _check(self, ok, what: str) -> None:
        if ok:
            return
        code, message = self._read_error()
        raise DexHandError(code, message or "{} failed".format(what))

    @property
    def error_code(self) -> SysErrorCode:
        """Code of the latest error; NONE when no error was reported."""
        self._require()
        code, _ = self._read_error()
        return code

    @property
    def error_message(self) -> str:
        """Message of the latest error; empty when no error was reported."""
        self._require()
        _, message = self._read_error()
        return message

    # -- topology and status ----------------------------------------------

    def get_hand_info(self) -> HandInfo:
        """Hand topology msg: side, board modules and pushers."""
        self._require()
        info = _HandInfo()
        self._check(self._lib.dexhand_get_hand_info(self._handle, ctypes.byref(info)),
                    "get_hand_info")

        modules = []
        for i in range(min(int(info.module_count), 2)):
            modules.append(ModuleInfo(
                module=HandModule(info.modules[i].module),
                version=PdoVersion(info.modules[i].version),
                op=bool(info.modules[i].op)))

        pushers = []
        for i in range(min(int(info.pusher_count), 2)):
            pushers.append(PusherInfo(
                id=PusherId(info.pushers[i].id),
                op=bool(info.pushers[i].op),
                has_force_sensor=bool(info.pushers[i].has_force_sensor)))

        return HandInfo(
            side=HandSide(info.side),
            module_count=int(info.module_count),
            pusher_count=int(info.pusher_count),
            modules=modules,
            pushers=pushers)

    def get_diagnostics(self) -> Diagnostics:
        """Transport and PDO diagnostics, including the working counter."""
        self._require()
        diagnostics = _Diagnostics()
        self._check(self._lib.dexhand_get_diagnostics(
            self._handle, ctypes.byref(diagnostics)), "get_diagnostics")
        return Diagnostics(
            adapter_available=bool(diagnostics.adapter_available),
            control_connected=bool(diagnostics.control_connected),
            maintenance_connected=bool(diagnostics.maintenance_connected),
            pdo_healthy=bool(diagnostics.pdo_healthy),
            expected_wkc=diagnostics.expected_wkc,
            last_wkc=diagnostics.last_wkc)

    def is_pdo_healthy(self) -> bool:
        """True when the last PDO cycle met the expected working counter."""
        return self.get_diagnostics().pdo_healthy

    def get_hand_status(self) -> Optional[StatusSnapshot]:
        """Latest status snapshot, or None before the first PDO frame.

        Returns None instead of raising when no snapshot is available yet.
        PDO keeps running while callbacks are disabled.
        """
        self._require()
        snapshot = _StatusSnapshot()
        if not self._lib.dexhand_get_hand_status(self._handle, ctypes.byref(snapshot)):
            return None
        return _status_from_c(snapshot)

    def set_status_callback(self, callback: Optional[Callable[[StatusSnapshot], None]]) -> None:
        """Register or clear the status callback.

        The callback runs on an SDK thread and must stay short; polling
        get_hand_status() is usually a better fit for Python. Use
        set_realtime_response() to control the callback rate.
        """
        self._require()

        if callback is None:
            self._lib.dexhand_set_status_callback(self._handle, None, None)
            self._status_cb = None
            self._user_status_cb = None
            return

        self._user_status_cb = callback
        if self._status_cb is None:
            self._status_cb = _StatusCallback(self._on_status)
        self._lib.dexhand_set_status_callback(
            self._handle, ctypes.cast(self._status_cb, ctypes.c_void_p), None)

    def set_error_callback(self, callback: Optional[Callable[[ErrorInfo], None]]) -> None:
        """Register or clear the error callback.

        The callback runs on the thread that detected the error and must stay
        short. error_code/error_message hold the latest error for polling.
        """
        self._require()

        if callback is None:
            self._lib.dexhand_set_error_callback(self._handle, None, None)
            self._error_cb = None
            self._user_error_cb = None
            return

        self._user_error_cb = callback
        if self._error_cb is None:
            self._error_cb = _ErrorCallback(self._on_error)
        self._lib.dexhand_set_error_callback(
            self._handle, ctypes.cast(self._error_cb, ctypes.c_void_p), None)

    def _on_status(self, pointer, _user) -> None:
        try:
            callback = self._user_status_cb
            if callback is None or not pointer:
                return
            callback(_status_from_c(pointer.contents))
        except BaseException as exc:  # never propagate into the SDK
            print("dexhand status callback error:", exc)

    def _on_error(self, pointer, _user) -> None:
        try:
            callback = self._user_error_cb
            if callback is None or not pointer:
                return
            callback(_error_from_c(pointer.contents))
        except BaseException as exc:
            print("dexhand error callback error:", exc)

    def listen(self, enable: bool = True) -> None:
        """Enable or disable status callbacks. PDO keeps running either way.

        Shares the enable flag with set_realtime_response(); the last call
        wins and the configured callback rate is kept.
        """
        self._require()
        self._check(self._lib.dexhand_listen(self._handle, 1 if enable else 0), "listen")

    def set_realtime_response(self, rate_hz: int, enable: bool = True) -> None:
        """Set the status callback rate in Hz and enable or disable callbacks.

        rate_hz is clamped to [100, 1000]. Uses the same enable flag as
        listen().
        """
        self._require()
        self._check(self._lib.dexhand_set_realtime_response(
            self._handle, int(rate_hz), 1 if enable else 0), "set_realtime_response")

    # -- motion ------------------------------------------------------------

    def set_control_mode(self, mode: ControlMode, force: bool = False) -> None:
        """Set the hand-wide control mode; both hand boards use the same mode.

        force=True first disables every joint. Raises DexHandError with
        MODE_CONFLICT when joints are enabled and the mode differs.
        """
        self._require()
        self._check(self._lib.dexhand_set_control_mode(
            self._handle, int(mode), 1 if force else 0), "set_control_mode")

    def get_control_mode(self) -> ControlMode:
        """Current hand-wide control mode."""
        self._require()
        mode = ctypes.c_int32()
        self._check(self._lib.dexhand_get_control_mode(
            self._handle, ctypes.byref(mode)), "get_control_mode")
        return ControlMode(int(mode.value))

    def set_hand_command(self, command: HandCommand) -> None:
        """Replace the whole-hand command frame.

        Joints with enable=False are disabled, even if a previous command
        enabled them.
        """
        self._require()
        native = command._to_c()
        self._check(self._lib.dexhand_set_hand_command(
            self._handle, ctypes.byref(native)), "set_hand_command")

    def get_hand_command(self) -> HandCommand:
        """Latest accepted whole-hand command frame."""
        self._require()
        native = _HandCommand()
        self._check(self._lib.dexhand_get_hand_command(
            self._handle, ctypes.byref(native)), "get_hand_command")

        joints = []
        for i in range(_MAX_JOINTS):
            target = native.joints[i]
            joints.append(JointTarget(
                target_deg=target.target_deg,
                speed_rpm=target.speed_rpm,
                current_ma=target.current_ma,
                kp=target.kp,
                kd=target.kd,
                enable=bool(target.enable)))
        return HandCommand(joints=joints)

    def move_joint(self, joint: JointId, target: JointTarget,
                   coupled_target: Optional[JointTarget] = None) -> None:
        """Update one joint target; other joints keep their commands.

        JOINT_POS and THREE_LOOP hold the coupled partner at its current angle
        automatically; coupled_target must be None there. In MIT, a coupled
        joint requires coupled_target with the partner's own kp/kd, while a
        non-coupled joint passes None.

        target_deg is in degrees. Raises DexHandError when the SDK rejects the
        command (wrong mode, missing partner, joint not enabled, ...).
        """
        self._require()

        native = target._to_c()
        native_coupled = None
        if coupled_target is not None:
            native_coupled = coupled_target._to_c()

        self._check(self._lib.dexhand_move_joint(
            self._handle, int(joint), ctypes.byref(native),
            ctypes.byref(native_coupled) if native_coupled is not None else None),
            "move_joint")

    def emergency_stop(self) -> None:
        """Disable every joint and clear the command slot.

        The connection stays open.
        """
        self._require()
        self._check(self._lib.dexhand_emergency_stop(self._handle), "emergency_stop")

    def reset_joints(self) -> None:
        """Move all joints to 0 degrees using the current mode and parameters."""
        self._require()
        self._check(self._lib.dexhand_reset_joints(self._handle), "reset_joints")

    # -- device information ------------------------------------------------

    def get_ctrl_firmware_version(self, part: FingerPart) -> FirmwareVersion:
        """CTRL device firmware version."""
        self._require()
        version = _FirmwareVersion()
        self._check(self._lib.dexhand_get_ctrl_firmware_version(
            self._handle, int(part), ctypes.byref(version)), "get_ctrl_firmware_version")
        return _firmware_from_c(version)

    def get_ec_firmware_version(self, module: HandModule) -> FirmwareVersion:
        """EC board firmware version."""
        self._require()
        version = _FirmwareVersion()
        self._check(self._lib.dexhand_get_ec_firmware_version(
            self._handle, int(module), ctypes.byref(version)), "get_ec_firmware_version")
        return _firmware_from_c(version)

    def get_current_temperature(self, module: HandModule) -> int:
        """hand board temperature in 0.01 Celsius.
        
        a temperature for thumb,a temperature for four-finger.
        """
        self._require()
        value = ctypes.c_int32()
        self._check(self._lib.dexhand_get_current_temperature(
            self._handle, int(module), ctypes.byref(value)), "get_current_temperature")
        return int(value.value)

    def get_safe_temperature(self, part: FingerPart) -> int:
        """Protection temperature threshold in Celsius."""
        self._require()
        value = ctypes.c_int32()
        self._check(self._lib.dexhand_get_safe_temperature(
            self._handle, int(part), ctypes.byref(value)), "get_safe_temperature")
        return int(value.value)

    def set_safe_temperature(self, part: FingerPart, celsius: int) -> None:
        """Set the protection temperature threshold in Celsius (>= 50)."""
        self._require()
        self._check(self._lib.dexhand_set_safe_temperature(
            self._handle, int(part), int(celsius)), "set_safe_temperature")

    def get_tactile(self, part: TactilePart) -> Optional[TactileData]:
        """Latest cached tactile data, or None before the first frame.

        Tactile frames rotate through the PDO; the cache is cleared on
        reconnect. Returns None instead of raising when no frame is available.
        """
        self._require()
        data = _TactileData()
        if not self._lib.dexhand_get_tactile(
                self._handle, int(part), ctypes.byref(data)):
            return None
        return _tactile_from_c(data)

    def read_ec_info(self) -> List[EcInfo]:
        """Information for each EC board: firmware, serial number, temperature."""
        self._require()
        total = int(self._lib.dexhand_read_ec_info(self._handle, None, 0))
        if total < 0:
            self._check(0, "read_ec_info")
        if total == 0:
            return []

        buffer = (_EcInfo * total)()
        written = int(self._lib.dexhand_read_ec_info(self._handle, buffer, total))
        if written < 0:
            self._check(0, "read_ec_info")
        return [_ec_info_from_c(buffer[i]) for i in range(min(written, total))]

    def read_device_info(self, part: FingerPart) -> DeviceInfo:
        """Full information block for one CTRL device."""
        self._require()
        info = _DeviceInfo()
        self._check(self._lib.dexhand_read_device_info(
            self._handle, int(part), ctypes.byref(info)), "read_device_info")
        return _device_info_from_c(info)

    # -- device operations -------------------------------------------------

    def restart_device(self, part: FingerPart) -> None:
        """Disable and re-enable one CTRL device."""
        self._require()
        self._check(self._lib.dexhand_restart_device(
            self._handle, int(part)), "restart_device")

    def set_fill_light(self, brightness: int) -> None:
        """Set fill-light brightness on the four-finger board (0=off, 255=max)."""
        self._require()
        self._check(self._lib.dexhand_set_fill_light(
            self._handle, int(brightness)), "set_fill_light")

    def set_ctrl_enable(self, part: FingerPart, on: bool = True) -> None:
        """Enable or disable one CTRL device."""
        self._require()
        self._check(self._lib.dexhand_set_ctrl_enable(
            self._handle, int(part), 1 if on else 0), "set_ctrl_enable")

    def restart_all_ctrl(self) -> None:
        """Disable and re-enable every CTRL device."""
        self._require()
        self._check(self._lib.dexhand_restart_all_ctrl(self._handle), "restart_all_ctrl")

    def request_restart_all_ec(self) -> None:
        """Ask every EC board to restart. Disconnect and reconnect afterwards."""
        self._require()
        self._lib.dexhand_request_restart_all_ec(self._handle)

    # -- pushers -----------------------------------------------------------

    @property
    def pusher_count(self) -> int:
        """Number of pushers found on the bus."""
        return int(self._lib.dexhand_pusher_count(self._handle)) if self._handle else 0

    def get_pusher_status(self, pusher: PusherId) -> PusherState:
        """Latest state snapshot of one pusher.

        The snapshot is updated by the PDO thread. Right after connect() it can
        still report online=False; poll until online before using pos or
        issuing commands.
        """
        self._require()
        state = _PusherState()
        self._check(self._lib.dexhand_get_pusher_status(
            self._handle, int(pusher), ctypes.byref(state)), "get_pusher_status")
        return _pusher_state_from_c(state)

    def set_pusher_command(self, pusher: PusherId, command: PusherCommand) -> None:
        """Set a pusher command in NONE, CSP or CSV mode.

        Changing the mode disables the drive; the next command must enable it
        again. fault_reset is consumed as a one-shot request.
        """
        self._require()
        native = command._to_c()
        self._check(self._lib.dexhand_set_pusher_command(
            self._handle, int(pusher), ctypes.byref(native)), "set_pusher_command")

    def get_pusher_command(self, pusher: PusherId) -> PusherCommand:
        """Last accepted pusher command."""
        self._require()
        native = _PusherCommand()
        self._check(self._lib.dexhand_get_pusher_command(
            self._handle, int(pusher), ctypes.byref(native)), "get_pusher_command")
        return _pusher_command_from_c(native)

    def move_pusher(self, pusher: PusherId, pos_um: int,
                    speed_um_per_s: int = 0) -> None:
        """Move a pusher in CSP mode.

        pos_um is the target position in micrometers; speed_um_per_s limits the
        speed and 0 uses the SDK default.
        """
        self._require()
        self._check(self._lib.dexhand_move_pusher(
            self._handle, int(pusher), int(pos_um), int(speed_um_per_s)), "move_pusher")

    def reset_pusher_fault(self, pusher: PusherId) -> None:
        """Request a one-shot pusher fault reset. The drive is disabled during reset."""
        self._require()
        self._check(self._lib.dexhand_reset_pusher_fault(
            self._handle, int(pusher)), "reset_pusher_fault")


__all__ = [
    "AdapterType",
    "ConnectStage",
    "ControlMode",
    "DeviceInfo",
    "DexHandError",
    "DexHandLibraryError",
    "DexHandPro",
    "Diagnostics",
    "EcInfo",
    "ErrorInfo",
    "FaultDomain",
    "FingerPart",
    "FirmwareVersion",
    "HandCommand",
    "HandInfo",
    "HandModule",
    "HandSide",
    "InterfaceInfo",
    "JointId",
    "JointState",
    "JointTarget",
    "ModuleInfo",
    "PdoVersion",
    "ProductType",
    "PusherCommand",
    "PusherField",
    "PusherId",
    "PusherInfo",
    "PusherMode",
    "PusherState",
    "SerialNumber",
    "StatusSnapshot",
    "SysErrorCode",
    "TactileData",
    "TactilePart",
    "scan_dex_interfaces",
    "scan_interfaces",
    "native_version",
    "native_abi_version",
    "version_info",
    "__version__",
]
