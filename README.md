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

## 功能特性

- 支持下载 YouTube 视频及播放列表
- 支持自定义视频分辨率
- 支持设置 HTTP/SOCKS 代理
- 支持 Cookie 文件导入
- 支持多种 JS 运行时（node/deno/bun/quickjs）

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

# 下载多个视频（空格分隔）
python youtube/downloader.py "https://www.youtube.com/watch?v=xxx https://www.youtube.com/watch?v=yyy"

# 指定分辨率和下载目录
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY" --folder ./downloads --resolution 720

# 使用代理和 Cookie
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY" --proxy socks5://127.0.0.1:10808 --cookies "C:\Env\www.youtube.com_cookies.txt"

# 完整示例
python youtube/downloader.py "https://www.youtube.com/watch?v=0xxrBVFNKeY" --proxy socks5://127.0.0.1:10808 --cookies "C:\Env\www.youtube.com_cookies.txt" --ffmpeg "C:\Env\ffmpeg-master-latest-win64-gpl\bin" --js-runtime node
```

## 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `urls` | 位置参数 | 必填 | 视频地址列表，支持多个地址（空格、逗号或分号分隔） |
| `--env` | 选项 | 无 | 环境配置文件路径（.env 文件） |
| `--folder` | 选项 | `videos` | 视频下载路径 |
| `--resolution` | 选项 | `1080` | 视频分辨率（如 1080、720、480） |
| `--ffmpeg` | 选项 | 无 | 设置 ffmpeg 路径 |
| `--proxy` | 选项 | 无 | 设置代理地址（如 `socks5://127.0.0.1:10808`） |
| `--cookies` | 选项 | 无 | Cookie 文件路径 |
| `--js-runtime` | 选项 | 无 | JS 运行时类型：`node` / `deno` / `bun` / `quickjs` |

## 环境配置文件

可通过 `--env` 参数指定 `.env` 配置文件，支持以下环境变量：

```env
# ffmpeg 路径
FFmpeg=C:\Env\ffmpeg-master-latest-win64-gpl\bin

# 代理地址
Proxy=socks5://127.0.0.1:10808
```
