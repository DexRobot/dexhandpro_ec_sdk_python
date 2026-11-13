"""
dexhand._types - public enums, data classes and C/Python conversions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional

from ._capi import (
    _DeviceInfo,
    _EcInfo,
    _ErrorInfo,
    _FirmwareVersion,
    _HandCommand,
    _JointState,
    _JointTarget,
    _MAX_JOINTS,
    _PusherCommand,
    _PusherState,
    _SerialNumber,
    _StatusSnapshot,
    _TACTILE_MAX_VALUES,
    _TactileData,
)


# ============================================================================
# enums
# ============================================================================

class HandSide(IntEnum):
    UNKNOWN = 0
    LEFT = 1
    RIGHT = 2


class HandModule(IntEnum):
    THUMB = 0
    FOUR_FINGER = 1
    UNKNOWN = 2


class TactilePart(IntEnum):
    THUMB_TIP = 0
    THUMB_PAD = 1
    INDEX_TIP = 2
    INDEX_PAD = 3
    MIDDLE_TIP = 4
    MIDDLE_PAD = 5
    RING_TIP = 6
    RING_PAD = 7
    LITTLE_TIP = 8
    LITTLE_PAD = 9
    PALM1 = 10
    PALM2 = 11
    PALM3 = 12
    PALM4 = 13
    THUMB_FORCE = 14
    PALM_FORCE = 15
    INDEX_MIDDLE_FORCE = 16
    RING_LITTLE_FORCE = 17
    COUNT = 18


class FingerPart(IntEnum):
    THUMB_DIST = 0
    THUMB_PROX = 1
    INDEX_PROX = 2
    MIDDLE_PROX = 3
    RING_PROX = 4
    LITTLE_PROX = 5
    INDEX_MIDDLE_DISTAL = 6
    RING_LITTLE_DISTAL = 7
    COUNT = 8


class JointId(IntEnum):
    THUMB_DIST = 0
    THUMB_MIDD = 1
    THUMB_PROX_SWNG = 2
    THUMB_PROX_FLEX = 3
    INDEX_PROX_SWNG = 4
    INDEX_PROX_FLEX = 5
    INDEX_DIST_COUPLED = 6
    MIDDLE_PROX_SWNG = 7
    MIDDLE_PROX_FLEX = 8
    MIDDLE_DIST_COUPLED = 9
    RING_PROX_SWNG = 10
    RING_PROX_FLEX = 11
    RING_DIST_COUPLED = 12
    LITTLE_PROX_SWNG = 13
    LITTLE_PROX_FLEX = 14
    LITTLE_DIST_COUPLED = 15
    COUNT = 16


class PusherId(IntEnum):
    PUSHER0 = 0
    PUSHER1 = 1
    COUNT = 2


class PusherMode(IntEnum):
    NONE = 0x00
    CSP = 0x08
    CSV = 0x09


class PusherField(IntEnum):
    STATUSWORD = 0
    MODE = 1
    POSITION = 2
    VELOCITY = 3
    TORQUE = 4
    CURRENT = 5
    FORCE = 6
    DC_LINK = 7
    FOLLOW_ERR = 8
    ERROR_CODE = 9
    ALARM_BITS = 10
    DRIVE_TEMP1 = 11
    DRIVE_TEMP2 = 12
    MOTOR_TEMP1 = 13
    MOTOR_TEMP2 = 14


class ControlMode(IntEnum):
    ZERO_TORQUE = 0x00
    JOINT_POS = 0x04
    THREE_LOOP = 0x06
    MIT = 0x07


class PdoVersion(IntEnum):
    UNKNOWN = 0
    V1_1 = 2


class ProductType(IntEnum):
    UNSUPPORTED = -1
    DX021_PRO = 0


class AdapterType(IntEnum):
    UNKNOWN = -1
    EC_SOEM = 1


class SysErrorCode(IntEnum):
    NONE = 0
    ADAPTER_NA = 1
    DEV_TYPE_MISMATCH = 2
    CONN_LOST = 3
    CONN_TIMEOUT = 4
    BOOT_FAILURE = 5
    PERMISSION_DENIED = 6
    DEPENDENCY_MISSING = 7
    INTERFACE_NOT_FOUND = 8
    NO_SLAVE_FOUND = 9
    PDO_LAYOUT_MISMATCH = 10
    PDO_UNHEALTHY = 11
    STATE_TRANSITION_FAILED = 12
    SDO_ABORT = 13
    SII_INVALID = 14
    UPGRADE_FAILED = 15
    MAINTENANCE_BUSY = 16
    INTERNAL = 17
    FIRMWARE_UPGRADE_REQUIRED = 18
    MODE_CONFLICT = 19
    MODE_NOT_SET = 20


class FaultDomain(IntEnum):
    NONE = 0
    ENVIRONMENT = 1
    HARDWARE = 2
    CONFIGURATION = 3
    DEVICE = 4
    SDK = 5


class ConnectStage(IntEnum):
    IDLE = 0
    INIT = 1
    CONFIG_INIT = 2
    CONFIG_MAP = 3
    IDENTIFY = 4
    SAFE_OP = 5
    OP = 6
    VERIFY = 7
    READY = 8


# ============================================================================
# dataclasses
# ============================================================================

@dataclass
class InterfaceInfo:
    name: str
    description: str


@dataclass
class JointState:
    online: bool = False
    over_current: bool = False
    over_temp: bool = False
    hall_fault: bool = False
    stall: bool = False
    angle_error: bool = False

    angle: int = 0              # 0.01 degree
    velocity: int = 0           # rpm
    current: int = 0            # mA
    hall: int = 0

    angle_primary: int = 0      # 0.01 degree
    angle_follower: int = 0     # 0.01 degree
    has_follower: bool = False
    angle_error_primary: bool = False
    angle_error_follower: bool = False


@dataclass
class StatusSnapshot:
    receive_timestamp: int      # steady_clock microseconds
    side: HandSide
    joints: List[JointState]


@dataclass
class ModuleInfo:
    module: HandModule
    version: PdoVersion
    op: bool


@dataclass
class PusherInfo:
    id: PusherId
    op: bool
    has_force_sensor: bool


@dataclass
class HandInfo:
    side: HandSide
    module_count: int
    pusher_count: int
    modules: List[ModuleInfo]
    pushers: List[PusherInfo]


@dataclass
class Diagnostics:
    adapter_available: bool
    control_connected: bool
    maintenance_connected: bool
    pdo_healthy: bool
    expected_wkc: int
    last_wkc: int


@dataclass
class FirmwareVersion:
    valid: bool
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        if not self.valid:
            return "invalid"
        return "{}.{}.{}".format(self.major, self.minor, self.patch)


@dataclass
class SerialNumber:
    valid: bool = False
    text: str = ""              # DX022-S-L-M-YYYYMMDDNNNN; empty when invalid


@dataclass
class EcInfo:
    valid: bool
    module: HandModule
    sys_id: int
    app_ver: int
    boot_ver: int
    hw_ver: int
    test_time: int
    sn: int                     # raw serial number
    serial: SerialNumber        # parsed sn
    status: int
    cur_temp: int               # 0.01 Celsius
    admin_on: bool


@dataclass
class DeviceInfo:
    valid: bool
    sys_id: int
    app_ver: int
    boot_ver: int
    hw_ver: int
    test_time: int
    app_len: int
    app_crc: int
    sn: int                     # raw serial number
    serial: SerialNumber        # parsed sn
    status: int
    cur_temp: int               # 0.01 Celsius
    proc_temp: int              # 0.01 Celsius
    iap_flag: int
    angle0_zero0: int
    angle0_zero1: int
    angle1_zero0: int
    angle1_zero1: int
    rated_cur: int
    rated_rpm: int
    rated_temp: int


@dataclass
class TactileData:
    values: List[int]
    count: int


@dataclass
class JointTarget:
    target_deg: float = 0.0
    speed_rpm: int = 0
    current_ma: int = 0
    kp: int = 0
    kd: int = 0
    enable: bool = False

    def _to_c(self) -> _JointTarget:
        out = _JointTarget()
        out.target_deg = float(self.target_deg)
        out.speed_rpm = int(self.speed_rpm)
        out.current_ma = int(self.current_ma)
        out.kp = int(self.kp)
        out.kd = int(self.kd)
        out.enable = 1 if self.enable else 0
        return out


@dataclass
class HandCommand:
    joints: List[JointTarget] = field(
        default_factory=lambda: [JointTarget() for _ in range(_MAX_JOINTS)])

    def _to_c(self) -> _HandCommand:
        out = _HandCommand()
        for i in range(_MAX_JOINTS):
            target = self.joints[i] if i < len(self.joints) else JointTarget()
            out.joints[i] = target._to_c()
        return out


@dataclass
class PusherState:
    online: bool
    enabled: bool
    fault: bool
    target_reached: bool       # raw DS402 bit 10; not asserted by every drive

    mapped: int
    mode: PusherMode
    mode_raw: int

    pos: int                    # um
    vel: int                    # um/s
    torque: int                 # 0.1% rated
    current: int                # 0.1% rated
    force: int                  # N
    dc_link_voltage: int        # mV
    following_error: int        # um
    error_code: int             # 0x603F
    alarm_bits: int             # 0x2201
    drive_temp: List[int]       # 0.1 Celsius
    motor_temp: List[int]       # 0.1 Celsius

    def has(self, field: PusherField) -> bool:
        return (self.mapped & (1 << int(field))) != 0


@dataclass
class PusherCommand:
    enable: bool = False
    fault_reset: bool = False
    mode: PusherMode = PusherMode.CSP
    pos: int = 0                # um
    vel: int = 0                # um/s

    def _to_c(self) -> _PusherCommand:
        out = _PusherCommand()
        out.enable = 1 if self.enable else 0
        out.fault_reset = 1 if self.fault_reset else 0
        out.mode = int(self.mode)
        out.pos = int(self.pos)
        out.vel = int(self.vel)
        return out


@dataclass
class ErrorInfo:
    code: SysErrorCode
    domain: FaultDomain
    stage: ConnectStage
    native_code: int
    message: str
    detail: str
    remedy: str


# ============================================================================
# exceptions
# ============================================================================

class DexHandError(Exception):
    """Operation failed. code/message mirror the SDK error report."""

    def __init__(self, code: SysErrorCode, message: str = ""):
        self.code = code
        self.message = message
        text = "{}: {}".format(code.name, message) if message else code.name
        super().__init__(text)


# ============================================================================
# conversions
# ============================================================================

def _decode_cstr(value) -> str:
    return bytes(value).split(b"\0", 1)[0].decode("utf-8", "replace")


def _index(value, enum_type, name: str, limit: int) -> int:
    """Validate an enum index in [0, limit) and return it as int."""
    try:
        index = int(enum_type(value))
    except ValueError:
        raise ValueError("invalid {}: {!r}".format(name, value)) from None
    if index < 0 or index >= limit:
        raise ValueError("invalid {}: {!r}".format(name, value))
    return index


def _int_in(value, low: int, high: int, name: str) -> int:
    """Validate an integer in [low, high] and return it as int."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError("invalid {}: {!r}".format(name, value)) from None
    if number < low or number > high:
        raise ValueError("{} out of range [{}, {}]: {}".format(name, low, high, number))
    return number


def _joint_from_c(src: _JointState) -> JointState:
    return JointState(
        online=bool(src.online),
        over_current=bool(src.over_current),
        over_temp=bool(src.over_temp),
        hall_fault=bool(src.hall_fault),
        stall=bool(src.stall),
        angle_error=bool(src.angle_error),
        angle=src.angle,
        velocity=src.velocity,
        current=src.current,
        hall=src.hall,
        angle_primary=src.angle_primary,
        angle_follower=src.angle_follower,
        has_follower=bool(src.has_follower),
        angle_error_primary=bool(src.angle_error_primary),
        angle_error_follower=bool(src.angle_error_follower),
    )


def _status_from_c(src: _StatusSnapshot) -> StatusSnapshot:
    return StatusSnapshot(
        receive_timestamp=src.receive_timestamp,
        side=HandSide(src.side),
        joints=[_joint_from_c(src.joints[i]) for i in range(_MAX_JOINTS)],
    )


def _firmware_from_c(src: _FirmwareVersion) -> FirmwareVersion:
    return FirmwareVersion(bool(src.valid), src.major, src.minor, src.patch)


def _serial_from_c(src: _SerialNumber) -> SerialNumber:
    return SerialNumber(
        valid=bool(src.valid),
        text=_decode_cstr(src.text),
    )


def _ec_info_from_c(src: _EcInfo) -> EcInfo:
    return EcInfo(
        valid=bool(src.valid),
        module=HandModule(src.module),
        sys_id=src.sys_id,
        app_ver=src.app_ver,
        boot_ver=src.boot_ver,
        hw_ver=src.hw_ver,
        test_time=src.test_time,
        sn=src.sn,
        serial=_serial_from_c(src.serial),
        status=src.status,
        cur_temp=src.cur_temp,
        admin_on=bool(src.admin_on),
    )


def _device_info_from_c(src: _DeviceInfo) -> DeviceInfo:
    return DeviceInfo(
        valid=bool(src.valid),
        sys_id=src.sys_id,
        app_ver=src.app_ver,
        boot_ver=src.boot_ver,
        hw_ver=src.hw_ver,
        test_time=src.test_time,
        app_len=src.app_len,
        app_crc=src.app_crc,
        sn=src.sn,
        serial=_serial_from_c(src.serial),
        status=src.status,
        cur_temp=src.cur_temp,
        proc_temp=src.proc_temp,
        iap_flag=src.iap_flag,
        angle0_zero0=src.angle0_zero0,
        angle0_zero1=src.angle0_zero1,
        angle1_zero0=src.angle1_zero0,
        angle1_zero1=src.angle1_zero1,
        rated_cur=src.rated_cur,
        rated_rpm=src.rated_rpm,
        rated_temp=src.rated_temp,
    )


def _tactile_from_c(src: _TactileData) -> TactileData:
    count = max(0, min(int(src.count), _TACTILE_MAX_VALUES))
    return TactileData(values=[int(src.values[i]) for i in range(count)], count=count)


def _pusher_state_from_c(src: _PusherState) -> PusherState:
    try:
        mode = PusherMode(src.mode)
    except ValueError:
        mode = PusherMode.NONE

    return PusherState(
        online=bool(src.online),
        enabled=bool(src.enabled),
        fault=bool(src.fault),
        target_reached=bool(src.target_reached),
        mapped=src.mapped,
        mode=mode,
        mode_raw=src.mode_raw,
        pos=src.pos,
        vel=src.vel,
        torque=src.torque,
        current=src.current,
        force=src.force,
        dc_link_voltage=src.dc_link_voltage,
        following_error=src.following_error,
        error_code=src.error_code,
        alarm_bits=src.alarm_bits,
        drive_temp=[src.drive_temp[0], src.drive_temp[1]],
        motor_temp=[src.motor_temp[0], src.motor_temp[1]],
    )


def _pusher_command_from_c(src: _PusherCommand) -> PusherCommand:
    try:
        mode = PusherMode(src.mode)
    except ValueError:
        mode = PusherMode.NONE

    return PusherCommand(
        enable=bool(src.enable),
        fault_reset=bool(src.fault_reset),
        mode=mode,
        pos=src.pos,
        vel=src.vel,
    )


def _error_from_c(src: _ErrorInfo) -> ErrorInfo:
    return ErrorInfo(
        code=SysErrorCode(src.code),
        domain=FaultDomain(src.domain),
        stage=ConnectStage(src.stage),
        native_code=src.native_code,
        message=_decode_cstr(src.message),
        detail=_decode_cstr(src.detail),
        remedy=_decode_cstr(src.remedy),
    )


