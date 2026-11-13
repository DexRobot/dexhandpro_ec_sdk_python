"""
dexhand._capi - ctypes ABI layer.

Keep this file limited to C structs, callback types, DLL loading and argtypes.
"""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
from typing import List


class DexHandLibraryError(RuntimeError):
    """The native library could not be loaded or reports an ABI mismatch."""


_ABI_VERSION = 1
_MAX_JOINTS = 16
_TACTILE_MAX_VALUES = 30
_INTERFACE_TEXT_MAX = 256
_ERROR_MESSAGE_MAX = 256
_ERROR_DETAIL_MAX = 512
_SERIAL_TEXT_MAX = 32


# ============================================================================
# ctypes structs
# ============================================================================

class _InterfaceInfo(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * _INTERFACE_TEXT_MAX),
        ("description", ctypes.c_char * _INTERFACE_TEXT_MAX),
    ]


class _JointState(ctypes.Structure):
    _fields_ = [
        ("online", ctypes.c_int32),
        ("over_current", ctypes.c_int32),
        ("over_temp", ctypes.c_int32),
        ("hall_fault", ctypes.c_int32),
        ("stall", ctypes.c_int32),
        ("angle_error", ctypes.c_int32),
        ("angle", ctypes.c_int32),
        ("velocity", ctypes.c_int32),
        ("current", ctypes.c_int32),
        ("hall", ctypes.c_int32),
        ("angle_primary", ctypes.c_int32),
        ("angle_follower", ctypes.c_int32),
        ("has_follower", ctypes.c_int32),
        ("angle_error_primary", ctypes.c_int32),
        ("angle_error_follower", ctypes.c_int32),
    ]


class _StatusSnapshot(ctypes.Structure):
    _fields_ = [
        ("receive_timestamp", ctypes.c_int64),
        ("side", ctypes.c_int32),
        ("joints", _JointState * _MAX_JOINTS),
    ]


class _ModuleInfo(ctypes.Structure):
    _fields_ = [
        ("module", ctypes.c_int32),
        ("version", ctypes.c_int32),
        ("op", ctypes.c_int32),
    ]


class _PusherInfo(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int32),
        ("op", ctypes.c_int32),
        ("has_force_sensor", ctypes.c_int32),
    ]


class _HandInfo(ctypes.Structure):
    _fields_ = [
        ("side", ctypes.c_int32),
        ("module_count", ctypes.c_int32),
        ("pusher_count", ctypes.c_int32),
        ("modules", _ModuleInfo * 2),
        ("pushers", _PusherInfo * 2),
    ]


class _Diagnostics(ctypes.Structure):
    _fields_ = [
        ("adapter_available", ctypes.c_int32),
        ("control_connected", ctypes.c_int32),
        ("maintenance_connected", ctypes.c_int32),
        ("pdo_healthy", ctypes.c_int32),
        ("expected_wkc", ctypes.c_uint32),
        ("last_wkc", ctypes.c_uint32),
    ]


class _FirmwareVersion(ctypes.Structure):
    _fields_ = [
        ("valid", ctypes.c_int32),
        ("major", ctypes.c_int32),
        ("minor", ctypes.c_int32),
        ("patch", ctypes.c_int32),
    ]


class _SerialNumber(ctypes.Structure):
    _fields_ = [
        ("valid", ctypes.c_int32),
        ("text", ctypes.c_char * _SERIAL_TEXT_MAX),
    ]


class _EcInfo(ctypes.Structure):
    _fields_ = [
        ("valid", ctypes.c_int32),
        ("module", ctypes.c_int32),
        ("sys_id", ctypes.c_uint32),
        ("app_ver", ctypes.c_uint32),
        ("boot_ver", ctypes.c_uint32),
        ("hw_ver", ctypes.c_uint32),
        ("test_time", ctypes.c_uint32),
        ("sn", ctypes.c_uint32),
        ("serial", _SerialNumber),
        ("status", ctypes.c_uint32),
        ("cur_temp", ctypes.c_int32),
        ("admin_on", ctypes.c_int32),
    ]


class _DeviceInfo(ctypes.Structure):
    _fields_ = [
        ("valid", ctypes.c_int32),
        ("sys_id", ctypes.c_uint32),
        ("app_ver", ctypes.c_uint32),
        ("boot_ver", ctypes.c_uint32),
        ("hw_ver", ctypes.c_uint32),
        ("test_time", ctypes.c_uint32),
        ("app_len", ctypes.c_uint32),
        ("app_crc", ctypes.c_uint32),
        ("sn", ctypes.c_uint32),
        ("serial", _SerialNumber),
        ("status", ctypes.c_uint32),
        ("cur_temp", ctypes.c_int32),
        ("proc_temp", ctypes.c_uint32),
        ("iap_flag", ctypes.c_uint32),
        ("angle0_zero0", ctypes.c_uint32),
        ("angle0_zero1", ctypes.c_uint32),
        ("angle1_zero0", ctypes.c_uint32),
        ("angle1_zero1", ctypes.c_uint32),
        ("rated_cur", ctypes.c_uint32),
        ("rated_rpm", ctypes.c_uint32),
        ("rated_temp", ctypes.c_uint32),
    ]


class _TactileData(ctypes.Structure):
    _fields_ = [
        ("values", ctypes.c_uint16 * _TACTILE_MAX_VALUES),
        ("count", ctypes.c_int32),
    ]


class _JointTarget(ctypes.Structure):
    _fields_ = [
        ("target_deg", ctypes.c_float),
        ("speed_rpm", ctypes.c_int32),
        ("current_ma", ctypes.c_int32),
        ("kp", ctypes.c_int32),
        ("kd", ctypes.c_int32),
        ("enable", ctypes.c_int32),
    ]


class _HandCommand(ctypes.Structure):
    _fields_ = [
        ("joints", _JointTarget * _MAX_JOINTS),
    ]


class _PusherState(ctypes.Structure):
    _fields_ = [
        ("online", ctypes.c_int32),
        ("enabled", ctypes.c_int32),
        ("fault", ctypes.c_int32),
        ("target_reached", ctypes.c_int32),
        ("mapped", ctypes.c_uint32),
        ("mode", ctypes.c_int32),
        ("mode_raw", ctypes.c_int32),
        ("pos", ctypes.c_int32),
        ("vel", ctypes.c_int32),
        ("torque", ctypes.c_int32),
        ("current", ctypes.c_int32),
        ("force", ctypes.c_int32),
        ("dc_link_voltage", ctypes.c_int32),
        ("following_error", ctypes.c_int32),
        ("error_code", ctypes.c_uint32),
        ("alarm_bits", ctypes.c_uint32),
        ("drive_temp", ctypes.c_int32 * 2),
        ("motor_temp", ctypes.c_int32 * 2),
    ]


class _PusherCommand(ctypes.Structure):
    _fields_ = [
        ("enable", ctypes.c_int32),
        ("fault_reset", ctypes.c_int32),
        ("mode", ctypes.c_int32),
        ("pos", ctypes.c_int32),
        ("vel", ctypes.c_int32),
    ]


class _ErrorInfo(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_int32),
        ("domain", ctypes.c_int32),
        ("stage", ctypes.c_int32),
        ("native_code", ctypes.c_int32),
        ("message", ctypes.c_char * _ERROR_MESSAGE_MAX),
        ("detail", ctypes.c_char * _ERROR_DETAIL_MAX),
        ("remedy", ctypes.c_char * _ERROR_DETAIL_MAX),
    ]


_StatusCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(_StatusSnapshot), ctypes.c_void_p)
_ErrorCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(_ErrorInfo), ctypes.c_void_p)


# ============================================================================
# native library loading
# ============================================================================

_lib = None
_dll_directory_handle = None


def _dll_candidates() -> List[Path]:
    package_dir = Path(__file__).resolve().parent
    names = [
        # Release package layout.
        Path("lib/windows/dexhandpro.dll"),
        # Lib source-tree build layouts.
        Path("build/x64-release/bin/Release/dexhandpro.dll"),
        Path("build/x64-debug/bin/Debug/dexhandpro.dll"),
    ]
    candidates = []
    for root in [package_dir] + list(package_dir.parents)[:4]:
        for name in names:
            candidates.append(root / name)
    return candidates


def _find_dll():
    override = os.environ.get("DEXHANDPRO_DLL")
    if override:
        return Path(override)

    for candidate in _dll_candidates():
        if candidate.is_file():
            return candidate

    # Fall back to the OS search path.
    return "dexhandpro.dll"


def _load_dll():
    global _dll_directory_handle

    path = _find_dll()

    try:
        if isinstance(path, Path):
            directory = str(path.parent)
            if os.name == "nt" and hasattr(os, "add_dll_directory"):
                # Keep the handle alive for the process lifetime so dependent
                # DLLs in the same directory stay resolvable.
                _dll_directory_handle = os.add_dll_directory(directory)
            return ctypes.CDLL(str(path))

        return ctypes.CDLL(path)
    except OSError as exc:
        raise DexHandLibraryError(
            "cannot load {}: {}. Install Npcap (WinPcap API compatible mode) "
            "and run as Administrator; or set DEXHANDPRO_DLL.".format(path, exc)
        ) from exc


def _bind(lib) -> None:
    lib.dexhand_c_abi_version.argtypes = []
    lib.dexhand_c_abi_version.restype = ctypes.c_uint32

    lib.dexhand_sdk_version.argtypes = []
    lib.dexhand_sdk_version.restype = ctypes.c_char_p

    lib.dexhand_scan_interfaces.argtypes = [
        ctypes.c_int32, ctypes.POINTER(_InterfaceInfo), ctypes.c_int32, ctypes.c_int32]
    lib.dexhand_scan_interfaces.restype = ctypes.c_int32

    lib.dexhand_create.argtypes = [ctypes.c_int32, ctypes.c_char_p]
    lib.dexhand_create.restype = ctypes.c_void_p

    lib.dexhand_destroy.argtypes = [ctypes.c_void_p]
    lib.dexhand_destroy.restype = None

    lib.dexhand_connect.argtypes = [ctypes.c_void_p, ctypes.c_int32]
    lib.dexhand_connect.restype = ctypes.c_int32
    lib.dexhand_disconnect.argtypes = [ctypes.c_void_p]
    lib.dexhand_disconnect.restype = ctypes.c_int32

    for name in ("dexhand_is_connected", "dexhand_is_available",
                 "dexhand_is_listening", "dexhand_product_type",
                 "dexhand_error_code", "dexhand_emergency_stop",
                 "dexhand_reset_joints", "dexhand_restart_all_ctrl",
                 "dexhand_pusher_count"):
        func = getattr(lib, name)
        func.argtypes = [ctypes.c_void_p]
        func.restype = ctypes.c_int32

    lib.dexhand_error_message.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_char), ctypes.c_int32]
    lib.dexhand_error_message.restype = ctypes.c_int32

    lib.dexhand_get_hand_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(_HandInfo)]
    lib.dexhand_get_hand_info.restype = ctypes.c_int32
    lib.dexhand_get_diagnostics.argtypes = [ctypes.c_void_p, ctypes.POINTER(_Diagnostics)]
    lib.dexhand_get_diagnostics.restype = ctypes.c_int32
    lib.dexhand_get_hand_status.argtypes = [ctypes.c_void_p, ctypes.POINTER(_StatusSnapshot)]
    lib.dexhand_get_hand_status.restype = ctypes.c_int32

    lib.dexhand_set_status_callback.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    lib.dexhand_set_status_callback.restype = None
    lib.dexhand_set_error_callback.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    lib.dexhand_set_error_callback.restype = None

    lib.dexhand_listen.argtypes = [ctypes.c_void_p, ctypes.c_int32]
    lib.dexhand_listen.restype = ctypes.c_int32
    lib.dexhand_set_realtime_response.argtypes = [
        ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32]
    lib.dexhand_set_realtime_response.restype = ctypes.c_int32

    lib.dexhand_set_control_mode.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32]
    lib.dexhand_set_control_mode.restype = ctypes.c_int32
    lib.dexhand_get_control_mode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int32)]
    lib.dexhand_get_control_mode.restype = ctypes.c_int32

    lib.dexhand_set_hand_command.argtypes = [ctypes.c_void_p, ctypes.POINTER(_HandCommand)]
    lib.dexhand_set_hand_command.restype = ctypes.c_int32
    lib.dexhand_get_hand_command.argtypes = [ctypes.c_void_p, ctypes.POINTER(_HandCommand)]
    lib.dexhand_get_hand_command.restype = ctypes.c_int32
    lib.dexhand_move_joint.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(_JointTarget),
        ctypes.POINTER(_JointTarget)]
    lib.dexhand_move_joint.restype = ctypes.c_int32

    lib.dexhand_get_ctrl_firmware_version.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(_FirmwareVersion)]
    lib.dexhand_get_ctrl_firmware_version.restype = ctypes.c_int32
    lib.dexhand_get_ec_firmware_version.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(_FirmwareVersion)]
    lib.dexhand_get_ec_firmware_version.restype = ctypes.c_int32

    for name in ("dexhand_get_current_temperature", "dexhand_get_safe_temperature"):
        func = getattr(lib, name)
        func.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32)]
        func.restype = ctypes.c_int32

    lib.dexhand_set_safe_temperature.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32]
    lib.dexhand_set_safe_temperature.restype = ctypes.c_int32

    lib.dexhand_get_tactile.argtypes = [ctypes.c_void_p, ctypes.c_int32,
                                        ctypes.POINTER(_TactileData)]
    lib.dexhand_get_tactile.restype = ctypes.c_int32

    lib.dexhand_read_ec_info.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(_EcInfo), ctypes.c_int32]
    lib.dexhand_read_ec_info.restype = ctypes.c_int32
    lib.dexhand_read_device_info.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(_DeviceInfo)]
    lib.dexhand_read_device_info.restype = ctypes.c_int32

    for name in ("dexhand_restart_device",
                 "dexhand_set_ctrl_enable", "dexhand_reset_pusher_fault"):
        func = getattr(lib, name)
        func.argtypes = [ctypes.c_void_p, ctypes.c_int32]
        func.restype = ctypes.c_int32

    lib.dexhand_set_fill_light.argtypes = [ctypes.c_void_p, ctypes.c_int32]
    lib.dexhand_set_fill_light.restype = ctypes.c_int32

    lib.dexhand_request_restart_all_ec.argtypes = [ctypes.c_void_p]
    lib.dexhand_request_restart_all_ec.restype = None

    lib.dexhand_get_pusher_status.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(_PusherState)]
    lib.dexhand_get_pusher_status.restype = ctypes.c_int32
    lib.dexhand_set_pusher_command.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(_PusherCommand)]
    lib.dexhand_set_pusher_command.restype = ctypes.c_int32
    lib.dexhand_get_pusher_command.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(_PusherCommand)]
    lib.dexhand_get_pusher_command.restype = ctypes.c_int32
    lib.dexhand_move_pusher.argtypes = [
        ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_uint32]
    lib.dexhand_move_pusher.restype = ctypes.c_int32


def _get_lib():
    global _lib
    if _lib is None:
        lib = _load_dll()

        try:
            _bind(lib)
        except AttributeError as exc:
            raise DexHandLibraryError(
                "dexhandpro.dll is missing C ABI symbols: {}".format(exc)) from exc

        abi = int(lib.dexhand_c_abi_version())
        if abi != _ABI_VERSION:
            raise DexHandLibraryError(
                "dexhandpro.dll ABI version {} does not match Python binding {}"
                .format(abi, _ABI_VERSION))

        _lib = lib
    return _lib


