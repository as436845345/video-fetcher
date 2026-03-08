# video-fetcher

YouTube 视频下载工具，基于 yt-dlp 实现。

---

## 目录

- [功能特性](#功能特性)
- [开发环境](#开发环境)
- [环境要求](#环境要求)
- [安装说明](#安装说明)
- [使用方法](#使用方法)
- [命令行参数](#命令行参数)
- [环境配置文件](#环境配置文件)
- [高级功能文档](#高级功能文档)

## 功能特性

- 支持下载 YouTube 视频及播放列表
- 支持自定义视频分辨率
- 支持设置 HTTP/SOCKS 代理
- 支持 Cookie 文件导入
- 支持多种 JS 运行时（node/deno/bun/quickjs）
- 支持将视频元信息保存为 JSON 文件

## 开发环境

- conda Python 3.12

## 环境要求

- Python 3.12+
- yt-dlp
- typer
- python-dotenv
- ffmpeg（可选，用于视频后处理）

## 安装说明

### 1. 克隆仓库

```bash
git clone https://github.com/as436845345/video-fetcher.git
cd video-fetcher
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

执行文件位于 `src/` 目录下：

```bash
cd src
python youtube/downloader.py <urls> [options]
```

### 基本示例

```bash
# 下载单个视频
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY"

# 下载多个视频（空格、逗号或分号分隔）
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx,https://www.youtube.com/watch?v=yyy"

# 指定分辨率
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY" --resolution 720

# 使用代理和 Cookie
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY" --proxy socks5://127.0.0.1:10808 --cookies "C:\Env\www.youtube.com_cookies.txt"

# 将视频信息保存为 JSON
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY" --metadata-to-json video_info.json

# 完整示例
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY" --proxy socks5://127.0.0.1:10808 --cookies "C:\Env\www.youtube.com_cookies.txt" --ffmpeg "C:\Env\ffmpeg-master-latest-win64-gpl\bin" --js-runtime node --metadata-to-json info.json
```

## 命令行参数

| 参数                   | 类型     | 默认值     | 说明                                                                       |
| ---------------------- | -------- | ---------- | -------------------------------------------------------------------------- |
| `urls`               | 位置参数 | 必填       | 视频地址列表，支持多个地址（空格、逗号或分号分隔）                         |
| `--env`              | 选项     | 无         | 环境配置文件路径（.env 文件）                                              |
| `--folder`           | 选项     | `videos` | 视频下载保存目录（当前版本仅预留参数）                                     |
| `--resolution`       | 选项     | `1080`   | 期望下载的视频最大分辨率（如 720、1080、2160）                             |
| `--ffmpeg`           | 选项     | 无         | 手动指定 ffmpeg 可执行文件路径                                             |
| `--proxy`            | 选项     | 无         | 设置网络代理（如 `http://127.0.0.1:7890`、`socks5://127.0.0.1:10808`） |
| `--cookies`          | 选项     | 无         | Cookie 文件路径（Netscape 格式）                                           |
| `--js-runtime`       | 选项     | 无         | JS 运行时类型：`node` / `deno` / `bun` / `quickjs`                 |
| `--metadata-to-json` | 选项     | 无         | 将 yt-dlp 返回的完整视频信息保存为 JSON 文件                               |

## 环境配置文件

可通过 `--env` 参数指定 `.env` 配置文件，支持以下环境变量：

```env
# ffmpeg 路径
FFmpeg=C:\Env\ffmpeg-master-latest-win64-gpl\bin

# 代理地址
Proxy=socks5://127.0.0.1:10808
```

---

## 高级功能文档

### Cookie 文件支持 (`--cookies`)

#### 功能说明

`--cookies` 选项用于加载 Netscape 格式的 Cookie 文件，使 yt-dlp 能够使用已登录的 Cookie 访问受限内容（如年龄限制视频、会员专享内容等）。

#### 使用示例

```bash
# 使用 Cookie 文件下载视频
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --cookies "C:\Env\www.youtube.com_cookies.txt"

# 结合代理使用
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --proxy socks5://127.0.0.1:10808 --cookies "C:\Env\www.youtube.com_cookies.txt"
```

> 详细文档：[`docs/yt-dlp/cookies-option-flow.md`](docs/yt-dlp/cookies-option-flow.md)

---

### JS 运行时支持 (`--js-runtime`)

#### 功能说明

`--js-runtime` 用于启用额外的 JavaScript 运行时，以便执行某些提取器所需的 JavaScript 代码（如 YouTube 的签名解密）。

#### 支持的运行时

| 运行时  | 可执行文件 | 最低支持版本 | 优先级           |
| ------- | ---------- | ------------ | ---------------- |
| deno    | `deno`   | 2.0.0        | 最高（默认启用） |
| node    | `node`   | 20.0.0       | 高               |
| quickjs | `qjs`    | 2023.12.9    | 中               |
| bun     | `bun`    | 1.0.31       | 低               |

#### 使用示例

```bash
# 使用 node 运行时
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --js-runtime node

# 指定运行时路径
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --js-runtime "node:/opt/node-20/bin/node"

# 启用多个运行时（高优先级优先使用）
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --js-runtime deno --js-runtime node

# 清除默认的 deno，只使用 node
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --js-runtime node
```

#### 调试信息

启用调试模式后，可查看 JS 运行时信息：

```
[debug] JS runtimes: deno 2.1.0, node 20.11.0
```

> 详细文档：[`docs/yt-dlp/js-runtimes-flow.md`](docs/yt-dlp/js-runtimes-flow.md)

---

### 元信息导出 (`--metadata-to-json`)

#### 功能说明

`--metadata-to-json` 选项用于将 yt-dlp 返回的完整视频元信息保存为 JSON 文件，便于后续处理或分析。

#### 导出的信息字段

- 视频标题、描述、时长
- 上传者信息
- 视频格式信息
- 缩略图 URL
- 观看次数、点赞数等统计信息
- 播放列表信息（如适用）

#### 使用示例

```bash
# 保存单个视频信息
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --metadata-to-json video_info.json

# 保存播放列表信息
python youtube/downloader.py "https://www.youtube.com/playlist?list=PLxxx" --metadata-to-json playlist_info.json

# 结合其他参数使用
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx" --proxy socks5://127.0.0.1:10808 --cookies cookies.txt --metadata-to-json info.json
```

#### JSON 文件结构示例

```json
[
  {
    "id": "video_id",
    "title": "视频标题",
    "description": "视频描述...",
    "duration": 180,
    "uploader": "上传者名称",
    "upload_date": "20240101",
    "view_count": 1000000,
    "like_count": 50000,
    "thumbnail": "https://i.ytimg.com/vi/xxx/maxresdefault.jpg",
    "formats": [...],
    "tags": ["tag1", "tag2"]
  }
]
```
