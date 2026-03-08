# `--js-runtimes` 调用流程

本文档详细说明 yt-dlp 中 `--js-runtimes` 参数的完整调用流程。

## 概述

`--js-runtimes` 用于启用额外的 JavaScript 运行时，以便执行某些提取器所需的 JavaScript 代码（如 YouTube 的签名解密）。

**支持的运行时**（按优先级从高到低）：
- `deno`（默认启用）
- `node`
- `quickjs`
- `bun`

---

## 1. 参数定义

**文件**: `yt_dlp/options.py:460-479`

```python
general.add_option(
    '--js-runtimes',
    metavar='RUNTIME[:PATH]',
    dest='js_runtimes',
    action='callback',
    callback=_list_from_options_callback,
    type='str',
    callback_kwargs={'delim': None},
    default=['deno'],
    help=(
        'Additional JavaScript runtime to enable, with an optional location for the runtime '
        '(either the path to the binary or its containing directory). '
        'This option can be used multiple times to enable multiple runtimes. '
        'Supported runtimes are (in order of priority, from highest to lowest): deno, node, quickjs, bun. '
        'Only "deno" is enabled by default. The highest priority runtime that is both enabled and '
        'available will be used. In order to use a lower priority runtime when "deno" is available, '
        '--no-js-runtimes needs to be passed before enabling other runtimes'))
```

**相关选项**:
- `--no-js-runtimes`: 清除所有已启用的运行时（包括默认值）

---

## 2. 参数解析

**文件**: `yt_dlp/__init__.py:783-785`

```python
js_runtimes = {
    runtime.lower(): {'path': config_path} for runtime, config_path in (
        [*arg.split(':', 1), None][:2] for arg in opts.js_runtimes)}
```

**解析示例**:
| 命令行参数 | 解析结果 |
|-----------|---------|
| `--js-runtimes deno` | `{'deno': {'path': None}}` |
| `--js-runtimes deno:/usr/bin/deno` | `{'deno': {'path': '/usr/bin/deno'}}` |
| `--js-runtimes node --js-runtimes bun` | `{'node': {'path': None}, 'bun': {'path': None}}` |

---

## 3. 运行时注册

**文件**: `yt_dlp/__init__.py:1098-1102`

```python
from .globals import supported_js_runtimes, supported_remote_components

supported_js_runtimes.value['deno'] = _DenoJsRuntime
supported_js_runtimes.value['node'] = _NodeJsRuntime
supported_js_runtimes.value['bun'] = _BunJsRuntime
supported_js_runtimes.value['quickjs'] = _QuickJsRuntime
```

**全局注册表**: `yt_dlp/globals.py:38`
```python
supported_js_runtimes = Indirect({})
```

---

## 4. 验证与清理

**文件**: `yt_dlp/YoutubeDL.py:735-736, 853-863`

### 4.1 初始化时设置默认值
```python
self.params['js_runtimes'] = self.params.get('js_runtimes', {'deno': {}})
self._clean_js_runtimes(self.params['js_runtimes'])
```

### 4.2 清理不支持的运行时
```python
def _clean_js_runtimes(self, runtimes):
    if not (
        isinstance(runtimes, dict)
        and all(isinstance(k, str) and (v is None or isinstance(v, dict)) for k, v in runtimes.items())
    ):
        raise ValueError('Invalid js_runtimes format, expected a dict of {runtime: {config}}')

    if unsupported_runtimes := runtimes.keys() - supported_js_runtimes.value.keys():
        self.report_warning(
            f'Ignoring unsupported JavaScript runtime(s): {", ".join(unsupported_runtimes)}.'
            f' Supported runtimes: {", ".join(supported_js_runtimes.value.keys())}.')
        for rt in unsupported_runtimes:
            runtimes.pop(rt)
```

---

## 5. 运行时实例化

**文件**: `yt_dlp/YoutubeDL.py:876-881`

```python
@functools.cached_property
def _js_runtimes(self):
    runtimes = {}
    for name, config in self.params.get('js_runtimes', {}).items():
        runtime_cls = supported_js_runtimes.value.get(name)
        runtimes[name] = runtime_cls(path=config.get('path')) if runtime_cls else None
    return runtimes
```

**特点**:
- 使用 `@functools.cached_property` 缓存实例，避免重复创建
- 按需实例化，仅在首次访问时创建

---

## 6. 运行时信息检测

**文件**: `yt_dlp/utils/_jsruntime.py`

### 6.1 基类定义
```python
class JsRuntime(abc.ABC):
    def __init__(self, path=None):
        self._path = path

    @functools.cached_property
    def info(self) -> JsRuntimeInfo | None:
        return self._info()

    @abc.abstractmethod
    def _info(self) -> JsRuntimeInfo | None:
        raise NotImplementedError
```

### 6.2 信息数据结构
```python
@dataclasses.dataclass(frozen=True)
class JsRuntimeInfo:
    name: str
    path: str
    version: str
    version_tuple: tuple[int, ...]
    supported: bool = True
```

### 6.3 各运行时实现

| 运行时 | 类 | 可执行文件 | 最低支持版本 |
|-------|-----|-----------|-------------|
| Deno | `DenoJsRuntime` | `deno` | 2.0.0 |
| Node | `NodeJsRuntime` | `node` | 20.0.0 |
| Bun | `BunJsRuntime` | `bun` | 1.0.31 |
| QuickJS | `QuickJsRuntime` | `qjs` | 2023.12.9 |

**示例 - Deno 实现**:
```python
class DenoJsRuntime(JsRuntime):
    MIN_SUPPORTED_VERSION = (2, 0, 0)

    def _info(self):
        path = _determine_runtime_path(self._path, 'deno')
        out = _get_exe_version_output(path, ['--version'])
        if not out:
            return None
        version = detect_exe_version(out, r'^deno (\S+)', 'unknown')
        vt = version_tuple(version, lenient=True)
        return JsRuntimeInfo(
            name='deno', path=path, version=version, version_tuple=vt,
            supported=vt >= self.MIN_SUPPORTED_VERSION)
```

---

## 7. 运行时使用

**文件**: `yt_dlp/extractor/youtube/jsc/_builtin/ejs.py:311`

```python
@property
def runtime_info(self) -> JsRuntimeInfo | None:
    runtime = self.ie._downloader._js_runtimes.get(self.JS_RUNTIME_NAME)
    if not runtime or not runtime.info or not runtime.info.supported:
        return None
    return runtime.info
```

**使用场景**:
- YouTube 签名解密
- 其他需要执行 JavaScript 的提取器

---

## 8. 调试信息输出

**文件**: `yt_dlp/YoutubeDL.py:4126-4137`

```python
if not self.params.get('js_runtimes'):
    write_debug('JS runtimes: none (disabled)')
else:
    write_debug('JS runtimes: %s' % (', '.join(sorted(
        f'{name} (unknown)' if runtime is None
        else join_nonempty(
            runtime.info.name,
            runtime.info.version + (' (unsupported)' if runtime.info.supported is False else ''),
        )
        for name, runtime in self._js_runtimes.items() if runtime is None or runtime.info is not None
    )) or 'none'))
```

**输出示例**:
```
[debug] JS runtimes: deno 2.1.0, node 20.11.0
```

---

## 完整流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        命令行参数解析                                    │
│  yt-dlp --js-runtimes deno --js-runtimes node:/usr/bin/node            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    options.py: 解析为列表                                │
│  ['deno', 'node:/usr/bin/node']                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    __init__.py: 转换为字典                               │
│  {'deno': {'path': None}, 'node': {'path': '/usr/bin/node'}}           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    YoutubeDL.__init__: 验证清理                          │
│  - 检查格式是否正确                                                      │
│  - 移除不支持的运行时                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              YoutubeDL._js_runtimes (cached_property)                  │
│  遍历配置 → 获取运行时类 → 实例化 (传入 path)                            │
│  {'deno': DenoJsRuntime(), 'node': NodeJsRuntime(path='...')}          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    首次访问 .info 属性时                                 │
│  - _determine_runtime_path: 查找可执行文件                               │
│  - _get_exe_version_output: 执行 --version                              │
│  - detect_exe_version: 解析版本号                                        │
│  - version_tuple: 转换为版本元组                                         │
│  - 检查是否 >= MIN_SUPPORTED_VERSION                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    提取器使用运行时                                      │
│  runtime = self.ie._downloader._js_runtimes.get('deno')                │
│  if runtime and runtime.info and runtime.info.supported:               │
│      # 执行 JavaScript 代码                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 使用示例

### 启用多个运行时
```bash
# 同时启用 deno 和 node
yt-dlp --js-runtimes deno --js-runtimes node <URL>

# 指定 node 路径
yt-dlp --js-runtimes node:/opt/node-20/bin/node <URL>
```

### 使用低优先级运行时
```bash
# 清除默认的 deno，只使用 node
yt-dlp --no-js-runtimes --js-runtimes node <URL>
```

### 禁用所有运行时
```bash
yt-dlp --no-js-runtimes <URL>
```
