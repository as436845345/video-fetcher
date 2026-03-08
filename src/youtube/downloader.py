import json  # 用于 JSON 序列化
import os  # 用于读取环境变量
import re  # 用于 URL 分割正则
from datetime import datetime  # 用于时间对象处理
from pathlib import Path  # 更安全的路径操作

from dotenv import load_dotenv  # 加载 .env 文件

import typer  # CLI 框架
from typing_extensions import Annotated  # 用于参数注解

import yt_dlp  # YouTube 下载工具

# 全局配置字典，用于存储 yt-dlp 相关参数
global_options = {}


def serialize_obj(obj):
    """
    自定义 JSON 序列化函数。

    yt-dlp 返回的数据中包含很多 Python 对象，
    例如 datetime、set、bytes 等，默认 json.dump 无法直接序列化。

    该函数用于在 json.dump 时自动转换这些对象。
    """

    # datetime -> ISO8601 字符串
    if isinstance(obj, datetime):
        return obj.isoformat()

    # 如果对象有 __dict__，直接序列化对象属性
    elif hasattr(obj, "__dict__"):
        return obj.__dict__

    # set/frozenset -> list
    elif isinstance(obj, (set, frozenset)):
        return list(obj)

    # bytes -> utf8 字符串
    elif isinstance(obj, bytes):
        return obj.decode("utf-8", errors="ignore")

    # 兜底方案：直接转换为字符串
    return str(obj)


def save_to_json(data: list | dict, output_path: str | Path):
    """
    将 Python 数据保存为 JSON 文件。

    参数:
        data:
            要保存的数据，可以是 list 或 dict
        output_path:
            JSON 文件保存路径
    """

    path = Path(output_path)  # 转换为 Path 对象

    # 自动创建父目录
    path.parent.mkdir(parents=True, exist_ok=True)

    # 写入 JSON 文件
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,  # 不转义中文
            indent=2,  # 美化 JSON 格式
            default=serialize_obj,  # 使用自定义序列化
        )

    # 打印保存路径
    print(f"✅ 已保存: {path.resolve()}")


def split_urls(urls: str):
    """
    将用户输入的 URL 字符串拆分成列表。

    支持以下分隔符:
        空格
        换行
        逗号
        分号

    示例:
        "url1 url2,url3" -> ["url1","url2","url3"]
    """

    # 使用正则拆分字符串
    return [url.strip() for url in re.split(r"[\s,;]+", urls) if url.strip()]


def validate_urls(urls: str):
    """
    验证 URL 是否为合法的 YouTube 地址。

    目前只允许:
        https://www.youtube.com/

    非法 URL 会被跳过。
    """

    url_list = split_urls(urls)  # 拆分 URL

    validated = []  # 存放合法 URL

    for url in url_list:
        # 判断 URL 前缀
        if url.startswith("https://www.youtube.com/"):
            validated.append(url)
        else:
            print(f"⚠️  跳过非 YouTube 地址: {url}")

    # 如果没有任何合法 URL
    if len(validated) == 0:
        print("不存在 url")
        exit(1)

    return validated


def set_env(env: str | None):
    """
    加载 .env 配置文件。

    支持配置:
        FFmpeg
        Proxy
    """

    if env is None:
        return  # 未指定 env 文件

    path = Path(env)

    if not path.exists():
        print(f"[ERROR] env={env} not exists!")

    # 加载 .env 文件
    load_dotenv(path)

    # 读取 ffmpeg 路径
    ffmpeg = os.getenv("FFmpeg", None)
    set_ffmpeg(ffmpeg)

    # 读取代理
    proxy = os.getenv("Proxy", None)
    set_proxy(proxy)


def set_ffmpeg(ffmpeg: str | None):
    """
    设置 ffmpeg 路径。

    yt-dlp 使用 ffmpeg 进行:
        - 合并视频
        - 转码
        - 音频处理
    """

    # https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/postprocessor/ffmpeg.py#L102
    global_options["ffmpeg"] = ffmpeg


def set_proxy(proxy: str | None):
    """
    设置 HTTP/SOCKS 代理。

    示例:
        http://127.0.0.1:7890
    """

    # https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L4163
    global_options["proxy"] = proxy


def set_cookies(cookies: str | None):
    """
    设置 cookies 文件。

    用途:
        - 下载会员视频
        - 访问年龄限制视频
        - 避免被 YouTube 限制

    cookies 文件通常从浏览器导出。
    """

    # https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L4179
    # https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/cookies.py#L93
    global_options["cookies"] = cookies


def set_js_runtime(js_runtime: str | None):
    """
    设置 JavaScript 运行时。

    yt-dlp 在解析 YouTube 时有时需要 JS runtime。

    支持:
        node
        deno
        bun
        quickjs
    """

    if js_runtime is not None:
        # https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L853
        global_options["js-runtime"] = {js_runtime: {}}


def get_videos_info(url_list: list[str]):
    """
    获取视频信息（不下载）。

    返回:
        list[dict]
    """

    # yt-dlp 配置
    options = {
        "proxy": global_options.get("proxy"),
        "cookiefile": global_options.get("cookies"),
        "js_runtimes": global_options.get("js-runtime"),
        "verbose": True,  # 打印详细日志
    }

    print(f"[get_videos_info] options={options}")

    video_info_list = []  # 存储所有视频信息

    # 创建 yt-dlp 下载器
    with yt_dlp.YoutubeDL(options) as downloader:  # type: ignore

        for url in url_list:
            # 提取视频信息（不下载）
            result = downloader.extract_info(url, download=False)

            if result is None:
                continue

            # 如果是播放列表
            if "entries" in result:
                video_info_list.extend(result["entries"])
            else:
                video_info_list.append(result)

    return video_info_list


def main(
    urls: str,
    env: Annotated[
        str | None,
        typer.Option(help="指定 .env 配置文件路径，用于加载代理、FFmpeg 等配置"),
    ] = None,
    folder: Annotated[
        str | None,
        typer.Option(help="视频下载保存目录（当前版本仅预留参数）"),
    ] = "videos",
    resolution: Annotated[
        int,
        typer.Option(help="期望下载的视频最大分辨率，例如 720 / 1080 / 2160"),
    ] = 1080,
    ffmpeg: Annotated[
        str | None,
        typer.Option(help="手动指定 ffmpeg 可执行文件路径"),
    ] = None,
    proxy: Annotated[
        str | None,
        typer.Option(help="设置网络代理，例如 http://127.0.0.1:7890"),
    ] = None,
    cookies: Annotated[
        str | None,
        typer.Option(help="cookies.txt 文件路径，用于访问受限视频"),
    ] = None,
    js_runtime: Annotated[
        str | None,
        typer.Option(help="指定 JS runtime: node / deno / bun / quickjs"),
    ] = None,
    metadata_to_json: Annotated[
        str | None,
        typer.Option(help="将 yt-dlp 返回的完整视频信息保存为 JSON 文件"),
    ] = None,
):
    """
    CLI 主入口。

    功能:
        - 验证 URL
        - 加载环境配置
        - 获取视频 metadata
        - 可选保存 JSON 信息
    """

    # 验证并拆分 URL
    url_list = validate_urls(urls)

    # 加载环境变量
    set_env(env)

    # 覆盖配置
    set_ffmpeg(ffmpeg)
    set_proxy(proxy)
    set_cookies(cookies)
    set_js_runtime(js_runtime)

    # 打印参数
    print(f"url={url_list}")
    print(f"options={global_options}")

    # 获取视频信息
    video_info_list = get_videos_info(url_list)

    # 如果需要保存 JSON
    if metadata_to_json is not None:
        save_to_json(video_info_list, metadata_to_json)


if __name__ == "__main__":
    # 启动 Typer CLI
    typer.run(main)
