# DexHand021Pro EtherCAT SDK —— Python 用户接口文档

| **项目**      | **内容**                                   |
| ------------- | ------------------------------------------ |
| 文档版本      | 1.0.1                                      |
| 文档日期      | 2026-11-13                                 |
| Python 包版本 | `dexhand.__version__`，当前 `"1.0.1"`      |
| 原生 SDK 版本 | `dexhand.native_version()`，当前 `"1.0.2"` |
| 原生接口版本  | `dexhand.native_abi_version()`，当前 `1`   |
| 适用产品      | DexHand021Pro                              |
| 适用固件      | 手板 EC 应用 V1.1（仅 V1.1）               |
| 通信方式      | EtherCAT（SOEM，经 `dexhandpro.dll`）      |
| 支持平台      | Windows 10/11 x64，64 位 Python 3.8+       |

## 目录

1. [文档说明](#1-文档说明)
2. [运行环境与安装](#2-运行环境与安装)
3. [快速开始](#3-快速开始)
4. [实例创建与连接](#4-实例创建与连接)
5. [状态与回调](#5-状态与回调)
6. [控制模式](#6-控制模式)
7. [关节控制](#7-关节控制)
8. [推杆控制](#8-推杆控制)
9. [设备信息与温度](#9-设备信息与温度)
10. [触觉](#10-触觉)
11. [诊断与错误](#11-诊断与错误)
12. [设备操作](#12-设备操作)
13. [类型与枚举参考](#13-类型与枚举参考)
14. [已知限制](#14-已知限制)
15. [常见问题](#15-常见问题)
16. [单位约定](#16-单位约定)
17. [修订记录](#17-修订记录)

---

## 1. 文档说明

本文档面向使用 DexHand021Pro Python SDK 的开发者，说明 `dexhand` 模块对外公开的类、函数、枚举、数据类、异常和使用约束。

Python SDK 通过随包的 `dexhandpro.dll` 与手通信，纯 Python 实现，无需编译。

```python
import dexhand
from dexhand import DexHandPro, ControlMode, JointId, JointTarget
```

公开符号见 `dexhand.__all__`。

### 1.1 调用约定

- **动作方法**（`connect`、`set_*`、`move_*`、`restart_*` 等）成功返回 `None`，失败抛出 `DexHandError`。`connect()` 例外，返回 `self` 以便链式调用。
- **读取方法**（`get_*`、`read_*`）成功返回数据对象，失败抛出 `DexHandError`。
  - `get_hand_status()` 和 `get_tactile()` 在尚无数据时返回 `None`，不抛异常。
- **状态属性**（`connected`、`available`、`listening`、`pusher_count`、`product_type`）在实例关闭后返回安全默认值，不抛异常。
- **枚举**均为 `IntEnum`，可直接与整数比较，也可作为列表下标。
- **数据类**均为 `dataclass`，字段使用 `snake_case`。
- 单位约定见[第 16 节](#16-单位约定)。

### 1.2 版本接口

```python
dexhand.__version__           # Python 包版本，str
dexhand.native_version()      # 原生库 dexhandpro.dll 版本，str
dexhand.native_abi_version()  # 原生接口版本，int
dexhand.version_info()        # "python=1.0.1 native=1.0.2 abi=1"
```

Python 包与 `dexhandpro.dll` 的接口版本不匹配时，加载会抛出 `DexHandLibraryError`。

```python
import dexhand

print(dexhand.version_info())
if dexhand.native_abi_version() != 1:
    raise RuntimeError("unsupported dexhandpro.dll ABI")
```

---

## 2. 运行环境与安装

### 2.1 环境要求

| **项目** | **要求**                                           |
| -------- | -------------------------------------------------- |
| 操作系统 | Windows 10/11 x64                                  |
| Python   | **64 位** Python 3.8 及以上                        |
| 原生库   | `dexhandpro.dll`（随 SDK 提供，x64 Release）       |
| 网络依赖 | Npcap（需单独安装，不随 SDK 分发）                 |
| 运行库   | Microsoft Visual C++ 2015–2022 x64 Redistributable |

运行前确认：

- 已安装 Npcap，并勾选 **WinPcap API 兼容模式**。
- 已安装 Microsoft Visual C++ 2015–2022 x64 Redistributable。
- 使用 **64 位** Python。32 位解释器无法加载 x64 的 `dexhandpro.dll`。
- Npcap 默认只允许管理员访问网卡，运行程序通常需要**管理员权限**。

### 2.2 发布包结构

```text
DexProEC_SDK_Python/
├── README.md
├── dexhand/
│   ├── __init__.py       # 公共导出
│   ├── dexhand.py        # DexHandPro、scan_*、版本接口
│   ├── _capi.py          # ctypes 结构体、DLL 加载、argtypes
│   └── _types.py         # 枚举、数据类、异常、类型转换
├── examples/
│   ├── scan.py           # 列出网卡，标注带从站的网口
│   ├── status_poll.py    # 手信息 + 关节角度轮询
│   ├── device_info.py    # EC / CTRL 设备信息
│   ├── tactile.py        # 触觉轮询
│   ├── pusher.py         # 推杆移动
│   └── move_joint.py     # 单关节移动
└── lib/
    └── windows/
        └── dexhandpro.dll
```

发布包以**源码目录**形式提供。使用时把 SDK 根目录加入 `sys.path`：

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\path\to\DexProEC_SDK_Python")))
import dexhand
```

也可以设置 `PYTHONPATH`，或把 `dexhand` 目录复制到项目目录中。`examples/` 下的脚本已内置同样的路径处理，可直接运行。

### 2.3 原生库加载顺序

`dexhand` 按以下顺序查找 `dexhandpro.dll`：

1. 环境变量 `DEXHANDPRO_DLL` 指定的完整路径；
2. 包目录及其最多 4 级父目录下的
   - `lib/windows/dexhandpro.dll`
   - `build/x64-release/bin/Release/dexhandpro.dll`
   - `build/x64-debug/bin/Debug/dexhandpro.dll`
3. 操作系统 DLL 搜索路径。

推荐直接使用随包的 `lib/windows/dexhandpro.dll`。如需指定其他位置：

```powershell
$env:DEXHANDPRO_DLL = "D:\path\to\Release\dexhandpro.dll"
```

注意：

- 加载失败或 DLL 接口版本不匹配时抛出 `DexHandLibraryError`。

---

## 3. 快速开始

### 3.1 第一步：查找网卡

```powershell
python examples/scan.py
```

输出中 `EtherCAT` 列为 `yes` 的网口即为可用网口，其 `interface` 名称用于后续所有示例：

```text
interface                                            description                                    EtherCAT
\Device\NPF_{EAD2C5A0-...}                           Intel(R) Ethernet Connection (24) I219-V       yes
```

未检测到从站时，脚本返回非零退出码，并提示检查供电、网线、Npcap 和管理员权限。

### 3.2 读取状态

```python
import time
from dexhand import DexHandPro, JointId, scan_dex_interfaces

interfaces = scan_dex_interfaces()
if not interfaces:
    raise SystemExit("no interface with EtherCAT slaves found")

with DexHandPro(interfaces[0].name) as hand:
    try:
        hand.connect()

        status = None
        for _ in range(50):
            status = hand.get_hand_status()
            if status is not None:
                break
            time.sleep(0.1)

        if status is None:
            raise RuntimeError("no status snapshot")

        print(status.side.name)
        print(status.joints[JointId.THUMB_DIST].angle / 100.0)   # 0.01° → °
    finally:
        hand.disconnect()
```

### 3.3 关节运动

完整示例见 `examples/move_joint.py`。核心流程（省略 import 与连接代码）：

```python
hand.set_control_mode(ControlMode.JOINT_POS)
hand.move_joint(JointId.INDEX_DIST_COUPLED, JointTarget(
    target_deg=current_deg + 10.0,
    speed_rpm=10000,
    current_ma=70,
    kp=464,
    kd=0,
    enable=True,
))
```

> **运动命令会驱动真实硬件。** 运行前确认手周围无障碍物，并准备好 `hand.emergency_stop()`。

### 3.4 示例清单

| **文件**         | **用途**                                | **是否驱动硬件** |
| ---------------- | --------------------------------------- | ---------------- |
| `scan.py`        | 列出网卡，标注带 EtherCAT 从站的网口    | 否               |
| `status_poll.py` | 手信息、EC 固件版本、诊断、关节角度轮询 | 否               |
| `device_info.py` | EC 板 / CTRL 设备信息、序列号、温度     | 否               |
| `tactile.py`     | 触觉区域轮询                            | 否               |
| `pusher.py`      | 推杆前进 1 mm，回原位后失能             | 是               |
| `move_joint.py`  | 单关节 +10°，并回读角度                 | 是               |

所有示例都支持指定网卡；不传递时自动选择唯一带从站的网口：

```powershell
python examples/status_poll.py "\Device\NPF_{EAD2C5A0-...}"
```

### 3.5 初始化顺序

```text
scan_interfaces / scan_dex_interfaces
  → DexHandPro(if_name)
  → connect
  → set_control_mode
  → set_hand_command / move_joint          （手控制）
    set_pusher_command / move_pusher       （推杆控制）
  → get_hand_status / set_status_callback  （手状态）
    get_pusher_status                      （推杆状态）
  → emergency_stop                         （需要时）
  → disconnect
  → close
```

---

## 4. 实例创建与连接

### 4.1 scan_interfaces / scan_dex_interfaces

```python
def scan_interfaces(
    adapter: AdapterType = AdapterType.EC_SOEM,
    only_with_slaves: bool = False,
) -> List[InterfaceInfo]: ...

def scan_dex_interfaces(
    adapter: AdapterType = AdapterType.EC_SOEM,
) -> List[InterfaceInfo]: ...
```

- `scan_interfaces()`：列出系统中全部可用网口。
- `scan_dex_interfaces()`：只返回检测到 EtherCAT 从站的网口，等价于 `scan_interfaces(adapter, only_with_slaves=True)`。

返回 `InterfaceInfo` 列表，无结果时返回空列表。

| **InterfaceInfo 字段** | **类型** | **说明**                        |
| ---------------------- | -------- | ------------------------------- |
| `name`                 | `str`    | 网口名称，用于构造 `DexHandPro` |
| `description`          | `str`    | 物理网卡描述                    |

### 4.2 DexHandPro 构造

```python
class DexHandPro:
    def __init__(
        self,
        if_name: str,
        adapter: AdapterType = AdapterType.EC_SOEM,
    ) -> None: ...
```

创建一个实例并绑定到指定网口。构造后尚未连接，需要调用 `connect()`。

| **异常**              | **条件**                   |
| --------------------- | -------------------------- |
| `ValueError`          | `if_name` 为空             |
| `DexHandError`        | 原生实例创建失败           |
| `DexHandLibraryError` | 原生库无法加载或版本不匹配 |

### 4.3 connect

```python
def connect(self, listen: bool = True) -> "DexHandPro": ...
```

建立完整控制连接：

1. 打开网口，扫描并配置手和推杆；
2. 进入 OPERATIONAL，确认所有从站就绪且数据周期稳定；
3. 启动后台 PDO 线程，开始收发状态与控制帧。

| **参数** | **类型** | **说明**                                         |
| -------- | -------- | ------------------------------------------------ |
| `listen` | `bool`   | 初始是否允许状态回调上报；PDO 和状态快照始终运行 |

返回 `self`。失败抛出 `DexHandError`，可通过 `error_code` / `error_message` 获取原因。

注意：

- `connect()` 是阻塞操作，总线配置期间可能持续数秒。
- 不要在回调线程中调用 `connect()`。
- 控制连接只接受 V1.1 手板 PDO 布局；检测到 V1.0 时返回 `FIRMWARE_UPGRADE_REQUIRED`。
- `listen=True` 只是允许上报；还需通过 `set_status_callback()` 注册回调函数。

### 4.4 disconnect / close

```python
def disconnect(self) -> None: ...
def close(self) -> None: ...
```

`disconnect()` 关闭当前控制连接：

- 清空命令槽，失能所有关节；
- 停止 PDO 线程；
- 关闭适配器，释放网口。

断开后可以再次 `connect()`。

`close()` 清除回调并释放原生实例：

- 可重复调用；
- 未断开时会一并释放连接，但仍建议显式先 `disconnect()`；
- 关闭后大多数方法抛出 `DexHandError`，状态属性返回安全默认值。

### 4.5 上下文管理器

```python
def __enter__(self) -> "DexHandPro": ...
def __exit__(self, exc_type, exc_value, traceback) -> None: ...
```

上下文管理器只负责**释放资源**：

- `__enter__` 返回实例本身，**不会自动连接**，仍需显式调用 `connect()`；
- `__exit__` 调用 `close()`，即使代码中途抛出异常也会执行。

`close()` 会自动断开仍在活动的连接，因此最简单的写法是：

```python
with DexHandPro(if_name) as hand:
    hand.connect()
    ...
    # 离开 with 时自动 close()，活动连接一并断开
```

如果希望明确控制断开的时机，也可以在 `finally` 中显式调用 `disconnect()`：

```python
with DexHandPro(if_name) as hand:
    try:
        hand.connect()
        ...
    finally:
        hand.disconnect()
```

两种写法效果相同；显式 `disconnect()` 只是让断开动作出现在代码里，便于阅读和排查。

### 4.6 状态属性

| **属性**       | **类型**      | **说明**                         |
| -------------- | ------------- | -------------------------------- |
| `if_name`      | `str`         | 实例绑定的网口名称               |
| `connected`    | `bool`        | 是否处于控制连接状态             |
| `available`    | `bool`        | 原生适配器是否已打开             |
| `listening`    | `bool`        | 状态回调是否开启                 |
| `product_type` | `ProductType` | 产品类型；关闭后为 `UNSUPPORTED` |

以上属性只读；关闭后 `connected`、`available`、`listening` 均为 `False`。

### 4.7 get_hand_info

```python
def get_hand_info(self) -> HandInfo: ...
```

返回连接时缓存的拓扑信息，不额外与手通信。

```python
@dataclass
class HandInfo:
    side: HandSide
    module_count: int
    pusher_count: int
    modules: List[ModuleInfo]
    pushers: List[PusherInfo]
```

| **字段**       | **类型**           | **说明**                          |
| -------------- | ------------------ | --------------------------------- |
| `side`         | `HandSide`         | 左手 / 右手 / 未知                |
| `module_count` | `int`              | 手板数量（上限 2）                |
| `pusher_count` | `int`              | 推杆数量（上限 2）                |
| `modules`      | `List[ModuleInfo]` | 手板信息，长度等于 `module_count` |
| `pushers`      | `List[PusherInfo]` | 推杆信息，长度等于 `pusher_count` |

`ModuleInfo`：

| **字段**  | **类型**     | **说明**      |
| --------- | ------------ | ------------- |
| `module`  | `HandModule` | 手板角色      |
| `version` | `PdoVersion` | PDO 版本      |
| `op`      | `bool`       | 从站是否在 OP |

`PusherInfo`：

| **字段**           | **类型**   | **说明**           |
| ------------------ | ---------- | ------------------ |
| `id`               | `PusherId` | 推杆索引           |
| `op`               | `bool`     | 从站是否在 OP      |
| `has_force_sensor` | `bool`     | 是否映射了力传感器 |

---

## 5. 状态与回调

### 5.1 set_status_callback

```python
def set_status_callback(
    self,
    callback: Optional[Callable[[StatusSnapshot], None]],
) -> None: ...
```

注册或清除状态回调。传入 `None` 清除。

说明：

- 注册回调不会自动启动上报；需要 `connect(listen=True)`（默认）或 `listen(True)` / `set_realtime_response(rate, True)`。
- 回调运行在 SDK 的 PDO 线程上，必须保持简短。
- 回调中禁止阻塞，禁止调用 `connect()` / `disconnect()`，禁止调用设备信息类接口。
- 回调中抛出的异常会被捕获并打印，不会传播进 SDK。
- 禁止在回调内做耗时操作，可以仅用回调获取数据，在外部处理回调数据。
- Python 回调需要获取 GIL；高频回调有额外开销，通常轮询 `get_hand_status()` 更合适。

```python
def on_status(status):
    print(status.joints[0].angle / 100.0)

hand.set_status_callback(on_status)
```

### 5.2 set_error_callback

```python
def set_error_callback(
    self,
    callback: Optional[Callable[[ErrorInfo], None]],
) -> None: ...
```

注册或清除错误回调。回调参数为 `ErrorInfo`（见 [11.7](#117-errorinfo)），运行在检测到错误的线程上，必须保持简短。

### 5.3 get_hand_status

```python
def get_hand_status(self) -> Optional[StatusSnapshot]: ...
```

返回最近一次状态快照；收到第一帧 PDO 数据之前返回 `None`。

- 关闭状态回调不影响 PDO 线程（仅为不触发状态回调），也不影响快照更新；
- `connect()` 返回后，PDO 线程需要少量周期才会产出第一帧，建议轮询等待。

### 5.4 set_realtime_response / listen

```python
def set_realtime_response(self, rate_hz: int, enable: bool = True) -> None: ...
def listen(self, enable: bool = True) -> None: ...
```

两者**共用同一个回调开关**，后调用者生效；回调频率保持不变。

| **接口**                                 | **作用**                                        |
| ---------------------------------------- | ----------------------------------------------- |
| `set_realtime_response(rate_hz, enable)` | 设置回调频率（内部限制 100–1000 Hz）并开/关回调 |
| `listen(enable)`                         | 只开/关回调，沿用已设置的频率                   |
| `listening` 属性                         | 查询当前是否开启回调                            |

关闭回调不会停止 PDO 线程，也不会停止状态快照更新。

### 5.5 StatusSnapshot

```python
@dataclass
class StatusSnapshot:
    receive_timestamp: int      # steady_clock 微秒
    side: HandSide
    joints: List[JointState]    # 固定 16 项，按 JointId 索引
```

| **字段**            | **类型**           | **说明**                              |
| ------------------- | ------------------ | ------------------------------------- |
| `receive_timestamp` | `int`              | 主站收到该帧的时间，steady_clock 微秒 |
| `side`              | `HandSide`         | 左手 / 右手 / 未知                    |
| `joints`            | `List[JointState]` | 16 个语义关节状态，按 `JointId` 索引  |

```python
state = status.joints[JointId.INDEX_PROX_FLEX]
print(state.angle / 100.0)
```

### 5.6 JointState

| **字段**               | **类型** | **说明**                              |
| ---------------------- | -------- | ------------------------------------- |
| `online`               | `bool`   | 关节在线                              |
| `over_current`         | `bool`   | 过流标志                              |
| `over_temp`            | `bool`   | 过温标志                              |
| `hall_fault`           | `bool`   | Hall 故障                             |
| `stall`                | `bool`   | 堵转                                  |
| `angle_error`          | `bool`   | 角度错误                              |
| `angle`                | `int`    | 语义关节角度，0.01°                   |
| `velocity`             | `int`    | 电机转速，rpm                         |
| `current`              | `int`    | 电机电流，mA                          |
| `hall`                 | `int`    | Hall 值                               |
| `angle_primary`        | `int`    | Ang0，0.01°                           |
| `angle_follower`       | `int`    | Ang1，0.01°；仅带第二传感器的关节有效 |
| `has_follower`         | `bool`   | 是否具有第二角度传感器                |
| `angle_error_primary`  | `bool`   | Ang0 角度错误                         |
| `angle_error_follower` | `bool`   | Ang1 角度错误                         |

远端耦合关节的 `angle` 等于 `angle_primary + angle_follower`。

---

## 6. 控制模式

### 6.1 ControlMode

```python
class ControlMode(IntEnum):
    ZERO_TORQUE = 0x00
    JOINT_POS = 0x04
    THREE_LOOP = 0x06
    MIT = 0x07
```

| **模式**      | **说明**                               |
| ------------- | -------------------------------------- |
| `ZERO_TORQUE` | 零力矩模式；不允许使能关节             |
| `JOINT_POS`   | 关节位置模式                           |
| `THREE_LOOP`  | 三环模式                               |
| `MIT`         | MIT 控制模式，可逐关节设置 `kp` / `kd` |

控制模式是**整手级**的：两块手板使用同一个模式。

### 6.2 set_control_mode / get_control_mode

```python
def set_control_mode(self, mode: ControlMode, force: bool = False) -> None: ...
def get_control_mode(self) -> ControlMode: ...
```

| **参数** | **类型**      | **说明**                            |
| -------- | ------------- | ----------------------------------- |
| `mode`   | `ControlMode` | 目标模式                            |
| `force`  | `bool`        | `True` 时先失能所有关节，再切换模式 |

- 已有关节使能且模式不同、`force=False` 时抛出 `MODE_CONFLICT`；
- 在 `ZERO_TORQUE` 下使能关节会抛出 `MODE_NOT_SET`。

---

## 7. 关节控制

### 7.1 JointId

```python
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
```

| **关节**              | **说明**       | **角度范围（°）** | **耦合伙伴**       |
| --------------------- | -------------- | ----------------- | ------------------ |
| `THUMB_DIST`          | 拇指远端       | -16 ~ 86          | —                  |
| `THUMB_MIDD`          | 拇指中端       | -16 ~ 86          | —                  |
| `THUMB_PROX_SWNG`     | 拇指近端侧摆   | 3 ~ 86            | `THUMB_PROX_FLEX`  |
| `THUMB_PROX_FLEX`     | 拇指近端弯曲   | -16 ~ 80          | `THUMB_PROX_SWNG`  |
| `INDEX_PROX_SWNG`     | 食指近端侧摆   | -8 ~ 25           | `INDEX_PROX_FLEX`  |
| `INDEX_PROX_FLEX`     | 食指近端弯曲   | -3 ~ 81           | `INDEX_PROX_SWNG`  |
| `INDEX_DIST_COUPLED`  | 食指耦合远端   | -6 ~ 172          | —                  |
| `MIDDLE_PROX_SWNG`    | 中指近端侧摆   | -25 ~ 25          | `MIDDLE_PROX_FLEX` |
| `MIDDLE_PROX_FLEX`    | 中指近端弯曲   | -3 ~ 81           | `MIDDLE_PROX_SWNG` |
| `MIDDLE_DIST_COUPLED` | 中指耦合远端   | -6 ~ 172          | —                  |
| `RING_PROX_SWNG`      | 无名指近端侧摆 | -25 ~ 8           | `RING_PROX_FLEX`   |
| `RING_PROX_FLEX`      | 无名指近端弯曲 | -3 ~ 81           | `RING_PROX_SWNG`   |
| `RING_DIST_COUPLED`   | 无名指耦合远端 | -6 ~ 172          | —                  |
| `LITTLE_PROX_SWNG`    | 小指近端侧摆   | -25 ~ 4           | `LITTLE_PROX_FLEX` |
| `LITTLE_PROX_FLEX`    | 小指近端弯曲   | -3 ~ 81           | `LITTLE_PROX_SWNG` |
| `LITTLE_DIST_COUPLED` | 小指耦合远端   | -6 ~ 172          | —                  |

耦合远端关节（`*_DIST_COUPLED`）的角度是两个角度传感器读数之和，控制上仍作为一个目标值。

注意：

- `JointId.COUNT` 只是计数哨兵，不是有效关节，不能传给 `move_joint()`。

### 7.2 JointTarget

```python
@dataclass
class JointTarget:
    target_deg: float = 0.0
    speed_rpm: int = 0
    current_ma: int = 0
    kp: int = 0
    kd: int = 0
    enable: bool = False
```

| **字段**     | **类型** | **说明**       | **有效范围（协议定义）**              |
| ------------ | -------- | -------------- | ------------------------------------- |
| `target_deg` | `float`  | 目标角度，度   | 按关节角度范围，见 [7.1](#71-jointid) |
| `speed_rpm`  | `int`    | 目标速度，rpm  | 拇指 0–15000；四指 0–25000            |
| `current_ma` | `int`    | 电流限制，mA   | 0–120                                 |
| `kp`         | `int`    | MIT 位置增益   | -32768 ~ 32767                        |
| `kd`         | `int`    | MIT 阻尼增益   | -32768 ~ 32767                        |
| `enable`     | `bool`   | 是否使能该关节 | `True` / `False`                      |

说明：

- 电流低于 50 mA 时电机可能无法启动，50 mA 可正常运行；耦合关节的电流设置会影响联动运动。
- Python 层**不会裁剪**超范围值，超出协议范围的参数行为由设备决定，请在构造前自行校验。

### 7.3 HandCommand

```python
@dataclass
class HandCommand:
    joints: List[JointTarget]   # 默认 16 项
```

`joints` 按 `JointId` 索引；长度不足 16 时，缺少的项使用默认值。

### 7.4 set_hand_command / get_hand_command

```python
def set_hand_command(self, command: HandCommand) -> None: ...
def get_hand_command(self) -> HandCommand: ...
```

`set_hand_command()` 按**整帧**处理：`enable=False` 的关节会被失能，即使上一条命令使能过它。

`get_hand_command()` 返回最近一次被接受的整手命令，`joints` 始终为 16 项。

### 7.5 move_joint

```python
def move_joint(
    self,
    joint: JointId,
    target: JointTarget,
    coupled_target: Optional[JointTarget] = None,
) -> None: ...
```

只更新一个关节，其它关节保持原命令。

| **参数**         | **类型**                | **说明**                                  |
| ---------------- | ----------------------- | ----------------------------------------- |
| `joint`          | `JointId`               | 目标关节                                  |
| `target`         | `JointTarget`           | 该关节的新目标                            |
| `coupled_target` | `Optional[JointTarget]` | 耦合伙伴的目标；仅 MIT 模式的耦合关节需要 |

耦合关节规则：

| **控制模式**               | **coupled_target** | **说明**                         |
| -------------------------- | ------------------ | -------------------------------- |
| `JOINT_POS` / `THREE_LOOP` | 必须为 `None`      | SDK 自动把耦合伙伴保持在当前角度 |
| `MIT`（耦合关节）          | 必须提供           | 伙伴的 `kp` / `kd` 独立生效      |
| `MIT`（非耦合关节）        | 传 `None`          | 普通单关节更新                   |

失败时抛出 `DexHandError`，例如非 MIT 模式传入了 `coupled_target`、MIT 下耦合关节缺少伙伴目标、关节未使能等。

MIT 下更新耦合关节：

```python
hand.set_control_mode(ControlMode.MIT, force=True)
hand.move_joint(
    JointId.INDEX_PROX_FLEX,
    JointTarget(target_deg=30.0, kp=464, kd=10, enable=True),
    JointTarget(target_deg=0.0, kp=464, kd=10, enable=True),
)
```

### 7.6 reset_joints

```python
def reset_joints(self) -> None: ...
```

使用当前控制模式，把所有关节目标设为 0 并使能；速度、电流、`kp`、`kd` 保持当前值。

`ZERO_TORQUE` 模式下抛出 `MODE_NOT_SET`。

### 7.7 emergency_stop

```python
def emergency_stop(self) -> None: ...
```

切换到零力矩模式并清空命令槽：

- 所有关节失能；
- 不关闭连接，之后可继续下发命令。

---

## 8. 推杆控制

### 8.1 PusherId

```python
class PusherId(IntEnum):
    PUSHER0 = 0
    PUSHER1 = 1
    COUNT = 2
```

近拇指侧推杆为 `PUSHER0`，另一侧为 `PUSHER1`。`COUNT` 只是计数哨兵，不能传给推杆接口。

### 8.2 PusherState

```python
@dataclass
class PusherState:
    online: bool
    enabled: bool
    fault: bool
    target_reached: bool
    mapped: int
    mode: PusherMode
    mode_raw: int
    pos: int
    vel: int
    torque: int
    current: int
    force: int
    dc_link_voltage: int
    following_error: int
    error_code: int
    alarm_bits: int
    drive_temp: List[int]
    motor_temp: List[int]

    def has(self, field: PusherField) -> bool: ...
```

| **字段**          | **类型**     | **说明**                                                      |
| ----------------- | ------------ | ------------------------------------------------------------- |
| `online`          | `bool`       | 已收到该推杆的 PDO 数据                                       |
| `enabled`         | `bool`       | 驱动器处于 Operation Enabled                                  |
| `fault`           | `bool`       | 驱动器故障位                                                  |
| `target_reached`  | `bool`       | 原始 DS402 状态字 bit10；并非所有驱动器都会置位（见下方说明） |
| `mapped`          | `int`        | 已映射 PDO 字段位图，配合 `PusherField` 使用                  |
| `mode`            | `PusherMode` | 公共模式映射；未知值映射为 `NONE`                             |
| `mode_raw`        | `int`        | 驱动器原始模式值                                              |
| `pos`             | `int`        | 实际位置，µm                                                  |
| `vel`             | `int`        | 实际速度，µm/s                                                |
| `torque`          | `int`        | 实际扭矩，0.1% 额定                                           |
| `current`         | `int`        | 实际电流，0.1% 额定                                           |
| `force`           | `int`        | 力传感器值，N                                                 |
| `dc_link_voltage` | `int`        | 母线电压，mV                                                  |
| `following_error` | `int`        | 跟随误差，µm                                                  |
| `error_code`      | `int`        | 驱动器错误码                                                  |
| `alarm_bits`      | `int`        | 驱动器报警位图                                                |
| `drive_temp`      | `List[int]`  | 驱动器温度，0.1℃，2 通道                                      |
| `motor_temp`      | `List[int]`  | 电机温度，0.1℃，2 通道                                        |

**`online`**：状态快照由 PDO 线程异步更新，`connect()` 返回后立即读取可能仍是 `online=False`。使用 `pos` 或下发命令前，请先确保轮询到 `online=True`（做法可以参考例程pusher.py -> wait_pusher_online）。

**`target_reached`**：直接映射 DS402 状态字 bit10，本驱动器不保证在位置模式下置位。判断到位建议使用编码器位置，例如 `abs(state.pos - target) <= 250`（µm）。

`has()` 用于判断某个 PDO 字段是否已映射：

```python
if state.has(PusherField.FORCE):
    print(state.force)
```

### 8.3 PusherMode / PusherCommand

```python
class PusherMode(IntEnum):
    NONE = 0x00
    CSP = 0x08
    CSV = 0x09

@dataclass
class PusherCommand:
    enable: bool = False
    fault_reset: bool = False
    mode: PusherMode = PusherMode.CSP
    pos: int = 0
    vel: int = 0
```

| **模式** | `pos`        | `vel`                                    | **说明**                       |
| -------- | ------------ | ---------------------------------------- | ------------------------------ |
| `NONE`   | 不使用       | 不使用                                   | 失能推杆                       |
| `CSP`    | 目标位置，µm | 最大速度，µm/s；0 表示默认最大速度 30000 | 周期同步位置模式，SDK 内部插补 |
| `CSV`    | 不使用       | 目标速度，µm/s；0 表示停止               | 周期同步速度模式，SDK 内部平滑 |

说明：

- 切换模式会复位使能序列，需要重新使能；
- `fault_reset` 是一次性请求，发送后自动清除；
- 行程限位有效时，`pos` 会被裁剪到限位范围内。

### 8.4 pusher_count / get_pusher_status

```python
@property
def pusher_count(self) -> int: ...

def get_pusher_status(self, pusher: PusherId) -> PusherState: ...
```

`pusher_count` 返回连接的推杆数量，实例关闭后为 `0`。

`get_pusher_status()` 返回最近一次 PDO 快照。刚连接时快照可能仍为初始值，建议轮询到 `state.online` 为 `True` 后再使用。

### 8.5 set_pusher_command / get_pusher_command

```python
def set_pusher_command(self, pusher: PusherId, command: PusherCommand) -> None: ...
def get_pusher_command(self, pusher: PusherId) -> PusherCommand: ...
```

下发 / 读取最近一次公共推杆命令。没有命令或当前模式不在公共接口范围内时，`get_pusher_command()` 抛出 `DexHandError`。

### 8.6 move_pusher

```python
def move_pusher(
    self,
    pusher: PusherId,
    pos_um: int,
    speed_um_per_s: int = 0,
) -> None: ...
```

以 CSP 模式移动到绝对位置。

| **参数**         | **类型**   | **说明**                           |
| ---------------- | ---------- | ---------------------------------- |
| `pusher`         | `PusherId` | 推杆索引                           |
| `pos_um`         | `int`      | 目标位置，µm                       |
| `speed_um_per_s` | `int`      | 最大速度，µm/s；0 使用默认值 30000 |

`speed_um_per_s` 对应原生 `uint32_t`，应传入非负值；负值会被按无符号数解释。

### 8.7 reset_pusher_fault

```python
def reset_pusher_fault(self, pusher: PusherId) -> None: ...
```

请求一次故障复位。复位期间推杆失能，复位后需要重新使能。

---

## 9. 设备信息与温度

本节接口需要与手板通信，每次调用会阻塞一小段时间；不要在状态回调或错误回调中调用。

### 9.1 get_ctrl_firmware_version

```python
def get_ctrl_firmware_version(self, part: FingerPart) -> FirmwareVersion: ...
```

读取指定 CTRL 设备的固件版本。

### 9.2 get_ec_firmware_version

```python
def get_ec_firmware_version(self, module: HandModule) -> FirmwareVersion: ...
```

读取指定手板 EC 的固件版本。

### 9.3 FirmwareVersion

```python
@dataclass
class FirmwareVersion:
    valid: bool
    major: int
    minor: int
    patch: int
```

`str(version)` 返回 `"major.minor.patch"`；`valid=False` 时返回 `"invalid"`。

### 9.4 get_current_temperature

```python
def get_current_temperature(self, module: HandModule) -> int: ...
```

读取手板 EC 当前温度，单位 **0.01℃**（例如 `5520` 表示 55.20℃）。

### 9.5 get_safe_temperature / set_safe_temperature

```python
def get_safe_temperature(self, part: FingerPart) -> int: ...
def set_safe_temperature(self, part: FingerPart, celsius: int) -> None: ...
```

读取 / 设置指定设备的保护温度阈值，单位 **℃**。`set_safe_temperature()` 拒绝小于 50 的值。

### 9.6 read_ec_info / EcInfo

```python
def read_ec_info(self) -> List[EcInfo]: ...
```

读取所有 EC 手板信息；没有数据时返回空列表。

| **字段**    | **类型**       | **说明**                                               |
| ----------- | -------------- | ------------------------------------------------------ |
| `valid`     | `bool`         | 信息是否有效                                           |
| `module`    | `HandModule`   | 手板                                                   |
| `sys_id`    | `int`          | 原始 SYS_ID                                            |
| `app_ver`   | `int`          | 原始应用版本；格式化版本用 `get_ec_firmware_version()` |
| `boot_ver`  | `int`          | 原始 Boot 版本                                         |
| `hw_ver`    | `int`          | 硬件版本                                               |
| `test_time` | `int`          | 原始测试时间戳                                         |
| `sn`        | `int`          | EC 序列号原始值                                        |
| `serial`    | `SerialNumber` | 解析后的序列号，见下方说明                             |
| `status`    | `int`          | EC 状态字（bit0 admin，bit1 触觉类型）                 |
| `cur_temp`  | `int`          | 当前温度，0.01℃                                        |
| `admin_on`  | `bool`         | Admin 模式                                             |

`SerialNumber`：

```python
@dataclass
class SerialNumber:
    valid: bool     # 存储的是合法出厂 SN
    text: str       # DX022-S-L-M-YYYYMMDDNNNN；无效时为空字符串
```

例如 `DX022-S-L-M-2026BBBDAABC` 表示 2026-11-13 生产、批次 12、左手。解析由 SDK 完成；序列号未写入或内容非法时 `valid=False`、`text` 为空。

```python
for info in hand.read_ec_info():
    print(info.module.name, info.serial.text if info.serial.valid else "not programmed")
```

### 9.7 read_device_info / DeviceInfo

```python
def read_device_info(self, part: FingerPart) -> DeviceInfo: ...
```

读取指定 CTRL 设备信息（以下信息并非都返回有效数据）。

| **字段**                        | **类型**       | **说明**                                                 |
| ------------------------------- | -------------- | -------------------------------------------------------- |
| `valid`                         | `bool`         | 信息是否有效                                             |
| `sys_id`                        | `int`          | 设备 SYS_ID                                              |
| `app_ver`                       | `int`          | 原始应用版本；格式化版本用 `get_ctrl_firmware_version()` |
| `boot_ver`                      | `int`          | 原始 Boot 版本                                           |
| `hw_ver`                        | `int`          | 硬件版本                                                 |
| `test_time`                     | `int`          | 原始测试时间戳                                           |
| `app_len`                       | `int`          | 应用镜像长度                                             |
| `app_crc`                       | `int`          | 应用镜像 CRC                                             |
| `sn`                            | `int`          | 设备序列号原始值                                         |
| `serial`                        | `SerialNumber` | 解析后的序列号，结构同 `EcInfo.serial`                   |
| `status`                        | `int`          | 设备状态字                                               |
| `cur_temp`                      | `int`          | 当前温度，0.01℃                                          |
| `proc_temp`                     | `int`          | 保护温度，0.01℃                                          |
| `iap_flag`                      | `int`          | IAP / Boot 标志                                          |
| `angle0_zero0` / `angle0_zero1` | `int`          | Ang0 零位标定，通道 0 / 1                                |
| `angle1_zero0` / `angle1_zero1` | `int`          | Ang1 零位标定，通道 0 / 1                                |
| `rated_cur`                     | `int`          | 额定电流                                                 |
| `rated_rpm`                     | `int`          | 额定转速                                                 |
| `rated_temp`                    | `int`          | 额定温度                                                 |

---

## 10. 触觉

### 10.1 TactilePart

```python
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
```

| **区域**                         | **有效通道数** |
| -------------------------------- | -------------- |
| 指尖 / 指腹（`*_TIP` / `*_PAD`） | 30             |
| 手掌（`PALM1`–`PALM4`）          | 24             |
| `THUMB_FORCE`                    | 2              |
| `PALM_FORCE`                     | 1              |
| `INDEX_MIDDLE_FORCE`             | 4              |
| `RING_LITTLE_FORCE`              | 4              |

`COUNT` 只是计数哨兵，不能传给 `get_tactile()`。

### 10.2 TactileData

```python
@dataclass
class TactileData:
    values: List[int]
    count: int
```

| **字段** | **类型**    | **说明**               |
| -------- | ----------- | ---------------------- |
| `values` | `List[int]` | 通道值，长度为 `count` |
| `count`  | `int`       | 有效通道数（0–30）     |

`values` 只包含有效通道，不做补零。

### 10.3 get_tactile

```python
def get_tactile(self, part: TactilePart) -> Optional[TactileData]: ...
```

返回该区域最近一次触觉数据；尚未收到时返回 `None`。

触觉帧按区域轮转上报，SDK 内部缓存每个区域最近一帧，重连时清空。

```python
data = hand.get_tactile(TactilePart.INDEX_TIP)
if data is not None:
    print(data.count, max(data.values, default=0))
```

---

## 11. 诊断与错误

### 11.1 get_diagnostics

```python
def get_diagnostics(self) -> Diagnostics: ...
```

```python
@dataclass
class Diagnostics:
    adapter_available: bool
    control_connected: bool
    maintenance_connected: bool
    pdo_healthy: bool
    expected_wkc: int
    last_wkc: int
```

| **字段**                | **说明**                                    |
| ----------------------- | ------------------------------------------- |
| `adapter_available`     | 适配器已打开                                |
| `control_connected`     | 控制连接已建立                              |
| `maintenance_connected` | 维护连接已建立（Python 接口不提供维护连接） |
| `pdo_healthy`           | 最近一次 PDO 周期满足期望 WKC               |
| `expected_wkc`          | 期望工作计数器                              |
| `last_wkc`              | 最近一次工作计数器                          |

### 11.2 is_pdo_healthy

```python
def is_pdo_healthy(self) -> bool: ...
```

等价于 `get_diagnostics().pdo_healthy`。

### 11.3 error_code / error_message

```python
@property
def error_code(self) -> SysErrorCode: ...

@property
def error_message(self) -> str: ...
```

读取最近一次系统级错误：无错误时 `error_code` 为 `SysErrorCode.NONE`，`error_message` 为空字符串。实例关闭后调用抛出 `DexHandError`。

### 11.4 异常类型

```python
class DexHandError(Exception):
    code: SysErrorCode
    message: str
```

所有原生接口失败时抛出。`str(exc)` 的格式为 `"CODE: message"`，没有消息时为 `"CODE"`。

```python
from dexhand import DexHandError, SysErrorCode

try:
    hand.set_control_mode(ControlMode.MIT)
except DexHandError as exc:
    if exc.code == SysErrorCode.MODE_CONFLICT:
        hand.set_control_mode(ControlMode.MIT, force=True)
```

```python
class DexHandLibraryError(RuntimeError):
    ...
```

原生库无法加载、DLL 与 Python 包版本不匹配时抛出。

构造 `DexHandPro` 时传入空 `if_name` 会抛出 `ValueError`。

### 11.5 SysErrorCode

```python
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
```

| **错误码**                  | **说明**               |
| --------------------------- | ---------------------- |
| `NONE`                      | 无错误                 |
| `ADAPTER_NA`                | 适配器不可用           |
| `DEV_TYPE_MISMATCH`         | 设备类型不匹配         |
| `CONN_LOST`                 | 连接丢失               |
| `CONN_TIMEOUT`              | 连接超时               |
| `BOOT_FAILURE`              | 启动失败               |
| `PERMISSION_DENIED`         | 权限不足               |
| `DEPENDENCY_MISSING`        | 依赖缺失               |
| `INTERFACE_NOT_FOUND`       | 网口不存在             |
| `NO_SLAVE_FOUND`            | 未发现从站             |
| `PDO_LAYOUT_MISMATCH`       | PDO 布局不匹配         |
| `PDO_UNHEALTHY`             | PDO 不健康             |
| `STATE_TRANSITION_FAILED`   | 从站状态切换失败       |
| `SDO_ABORT`                 | SDO 事务失败           |
| `SII_INVALID`               | SII 无效               |
| `UPGRADE_FAILED`            | 升级失败               |
| `MAINTENANCE_BUSY`          | 维护连接占用           |
| `INTERNAL`                  | SDK 内部错误           |
| `FIRMWARE_UPGRADE_REQUIRED` | 固件版本过低，需要升级 |
| `MODE_CONFLICT`             | 控制模式冲突           |
| `MODE_NOT_SET`              | 未设置控制模式         |

### 11.6 FaultDomain / ConnectStage

```python
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
```

| **FaultDomain** | **说明**                     |
| --------------- | ---------------------------- |
| `NONE`          | 未归因                       |
| `ENVIRONMENT`   | 运行环境（权限、网卡、依赖） |
| `HARDWARE`      | 总线 / 从站硬件              |
| `CONFIGURATION` | 参数或配置                   |
| `DEVICE`        | 设备侧                       |
| `SDK`           | SDK 内部                     |

| **ConnectStage** | **说明**    |
| ---------------- | ----------- |
| `IDLE`           | 空闲        |
| `INIT`           | 网口初始化  |
| `CONFIG_INIT`    | 从站配置    |
| `CONFIG_MAP`     | PDO 映射    |
| `IDENTIFY`       | 板型识别    |
| `SAFE_OP`        | SAFE_OP     |
| `OP`             | OPERATIONAL |
| `VERIFY`         | 校验        |
| `READY`          | 就绪        |

### 11.7 ErrorInfo

```python
@dataclass
class ErrorInfo:
    code: SysErrorCode
    domain: FaultDomain
    stage: ConnectStage
    native_code: int
    message: str
    detail: str
    remedy: str
```

| **字段**      | **说明**     |
| ------------- | ------------ |
| `code`        | 错误码       |
| `domain`      | 故障归因     |
| `stage`       | 发生阶段     |
| `native_code` | 原生错误码   |
| `message`     | 简短描述     |
| `detail`      | 详细诊断     |
| `remedy`      | 建议处理方式 |

---

## 12. 设备操作

### 12.1 restart_device

```python
def restart_device(self, part: FingerPart) -> None: ...
```

失能并重新使能指定 CTRL 设备。

### 12.2 set_ctrl_enable

```python
def set_ctrl_enable(self, part: FingerPart, on: bool = True) -> None: ...
```

使能或失能指定 CTRL 设备。

### 12.3 restart_all_ctrl

```python
def restart_all_ctrl(self) -> None: ...
```

失能并重新使能全部 CTRL 设备。

### 12.4 request_restart_all_ec

```python
def request_restart_all_ec(self) -> None: ...
```

请求全部 EC 手板重启：

- 手板立即复位，可能不会返回应答；
- 调用后需要 `disconnect()` 并重新 `connect()`。

### 12.5 set_fill_light

```python
def set_fill_light(self, brightness: int) -> None: ...
```

设置补光灯亮度，固定作用于四指板 EC 设备。

| **参数**     | **类型** | **说明**             |
| ------------ | -------- | -------------------- |
| `brightness` | `int`    | 0 关闭，255 最大亮度 |

对应原生 `uint8_t`，应传入 0–255。

---

## 13. 类型与枚举参考

### 13.1 HandSide / HandModule

```python
class HandSide(IntEnum):
    UNKNOWN = 0
    LEFT = 1
    RIGHT = 2

class HandModule(IntEnum):
    THUMB = 0
    FOUR_FINGER = 1
    UNKNOWN = 2
```

### 13.2 FingerPart

```python
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
```

| **枚举**              | **说明**               |
| --------------------- | ---------------------- |
| `THUMB_DIST`          | 拇指远端               |
| `THUMB_PROX`          | 拇指近端               |
| `INDEX_PROX`          | 食指近端               |
| `MIDDLE_PROX`         | 中指近端               |
| `RING_PROX`           | 无名指近端             |
| `LITTLE_PROX`         | 小指近端               |
| `INDEX_MIDDLE_DISTAL` | 食指和中指远端         |
| `RING_LITTLE_DISTAL`  | 无名指和小指远端       |
| `COUNT`               | 计数哨兵，不是有效设备 |

### 13.3 PdoVersion / ProductType / AdapterType

```python
class PdoVersion(IntEnum):
    UNKNOWN = 0
    V1_1 = 2

class ProductType(IntEnum):
    UNSUPPORTED = -1
    DX021_PRO = 0

class AdapterType(IntEnum):
    UNKNOWN = -1
    EC_SOEM = 1
```

### 13.4 PusherField

`PusherField` 用于 `PusherState.has()`，每一位对应一个已映射的 PDO 字段。

```python
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
```

| **枚举**      | **说明**     |
| ------------- | ------------ |
| `STATUSWORD`  | 状态字       |
| `MODE`        | 模式显示     |
| `POSITION`    | 实际位置     |
| `VELOCITY`    | 实际速度     |
| `TORQUE`      | 实际扭矩     |
| `CURRENT`     | 实际电流     |
| `FORCE`       | 力传感器值   |
| `DC_LINK`     | 母线电压     |
| `FOLLOW_ERR`  | 跟随误差     |
| `ERROR_CODE`  | 错误码       |
| `ALARM_BITS`  | 报警位图     |
| `DRIVE_TEMP1` | 驱动器温度 1 |
| `DRIVE_TEMP2` | 驱动器温度 2 |
| `MOTOR_TEMP1` | 电机温度 1   |
| `MOTOR_TEMP2` | 电机温度 2   |

---

## 14. 已知限制

1. **参数不自动校验。** 超出协议范围的参数不会被裁剪，行为由设备决定；请按[第 7.1 节](#71-jointid)和[第 7.2 节](#72-jointtarget)的范围传入。
2. **计数枚举不是有效索引。** 不要向接口传入 `JointId.COUNT`、`PusherId.COUNT`、`TactilePart.COUNT`、`FingerPart.COUNT`。
3. **回调与 GIL。** 状态/错误回调从 SDK 线程进入 Python，需要获取 GIL；不在回调中做耗时操作，高频场景优先轮询。
4. **关闭顺序。** 推荐 `disconnect()` → `close()`；上下文管理器只保证 `close()`。
5. **以源码目录分发。** 当前发布包不包含 wheel；通过 `sys.path` / `PYTHONPATH` 使用，DLL 查找规则见 [2.3](#23-原生库加载顺序)。
6. **关闭后行为不同。** 状态属性返回安全默认值，`get_*` / `set_*` / `error_code` / `error_message` 抛出 `DexHandError`。
7. **`THUMB_MIDD` 拼写。** 沿用既有拼写，含义为拇指中端。
8. **推杆到位判断。** `target_reached` 是驱动器原始状态位，本驱动器不保证置位；使用编码器位置判断到位。
9. **推杆状态异步更新。** `get_pusher_status()` 在首帧数据到达前返回初始值，使用前轮询 `online`。

---

## 15. 常见问题

### 15.1 加载 DLL 失败

```text
[WinError 193] %1 is not a valid Win32 application
```

使用了 32 位 Python 加载 x64 DLL。请改用 64 位 Python。

```text
[WinError 126] 找不到指定的模块
```

依赖 DLL 缺失，通常是 Npcap 或 VC++ 运行库。安装 Npcap（勾选 WinPcap API 兼容模式）和 Microsoft Visual C++ 2015–2022 x64 Redistributable。

```text
dexhandpro.dll is missing C ABI symbols
```

加载到了错误版本的 DLL。确认 `DEXHANDPRO_DLL` 指向本 SDK 的 `dexhandpro.dll`。

### 15.2 扫描不到网口或从站

- 确认网线、手部供电和 EtherCAT 拓扑；
- 确认已安装 Npcap，并以管理员权限运行；
- 先运行 `examples/scan.py`，检查网口是否出现在列表中；
- 如果仍为空，检查是否有其他程序占用了网卡。

### 15.3 推杆相关

**`online` 一直是 `False`**

状态快照由 PDO 线程更新，`connect()` 返回后需要等待第一帧。轮询 `get_pusher_status()`，通常几百毫秒内变为 `True`；持续为 `False` 时检查从站是否在 OP。

**`target_reached` 一直是 `False`**

该字段直接映射 DS402 状态字 bit10，本驱动器不保证在位置模式下置位。使用编码器位置判断到位：

```python
state = hand.get_pusher_status(PusherId.PUSHER0)
if abs(state.pos - target_um) <= 250:
    print("in position")
```

**推杆不动**

- 确认 `state.enabled` 为 `True`；
- 确认 `state.fault` 为 `False`，否则先 `reset_pusher_fault()`；
- 确认目标位置在行程限位内。

### 15.4 MODE_CONFLICT

有关节处于使能状态时切换模式会冲突：

```python
hand.set_control_mode(ControlMode.JOINT_POS, force=True)
```

或先调用 `hand.emergency_stop()`。

### 15.5 MODE_NOT_SET

`reset_joints()` 和使能关节的命令需要非零力矩模式：

```python
hand.set_control_mode(ControlMode.JOINT_POS)
```

### 15.6 PDO 不健康 / 从站掉到 SAFE_OP

- 检查 `get_diagnostics()` 中的 `expected_wkc` 与 `last_wkc`；
- 确认 PDO 周期内没有长时间阻塞总线；
- 检查 Npcap、管理员权限和网线连接；
- 断开后重新 `connect()`。

### 15.7 状态回调不触发

- 确认已调用 `set_status_callback(callback)`；
- 确认 `connect(listen=True)`，或 `listen(True)` / `set_realtime_response(rate, True)`；
- 确认 `listening` 为 `True`；
- 回调频率由 `set_realtime_response()` 控制。

---

## 16. 单位约定

| **数据**                                                    | **单位**          |
| ----------------------------------------------------------- | ----------------- |
| 关节角度（`JointState.angle`）                              | 0.01°             |
| 关节目标角度（`JointTarget.target_deg`）                    | 度                |
| 电机速度                                                    | rpm               |
| 电机电流                                                    | mA                |
| 关节增益 `kp` / `kd`                                        | 原始整数值        |
| EC / 设备温度                                               | 0.01℃             |
| 保护温度（`get_safe_temperature` / `set_safe_temperature`） | ℃                 |
| 推杆位置                                                    | µm                |
| 推杆速度                                                    | µm/s              |
| 推杆扭矩 / 电流                                             | 0.1% 额定         |
| 推杆力                                                      | N                 |
| 推杆温度                                                    | 0.1℃              |
| 触觉通道值                                                  | 原始传感器值      |
| `receive_timestamp`                                         | steady_clock 微秒 |

---

## 17. 修订记录

| **日期**   | **版本** | **说明**                                                                                                                                                                                                                                    |
| ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-11-13 | 1.0.1    | 全面校对接口：修正版本接口名称、包结构、示例清单、`get_hand_info` 缓存说明；按协议补充关节角度/速度/电流范围；补充 `move_joint` 耦合规则、`listen` / `set_realtime_response` 共用开关、序列号解析、推杆 `online` 与 `target_reached` 说明。 |
| 2026-11-12 | 1.0.1    | 初版 Python 用户接口文档。                                                                                                                                                                                                                  |
