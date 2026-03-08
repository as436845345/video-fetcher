"""
[urls]: 视频地址列表，可以多个地址
--folder [path]: 视频下载路径
--resolution: 视频分辨率
--ffmpeg [path]: 设置 ffmpeg 路径
--proxy [url]: 设置代理
--cookies [path]: 设置代理
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

import typer
from typing_extensions import Annotated

import yt_dlp

global_options = {}


def split_urls(urls: str):
    return [url.strip() for url in re.split(r"[\s,;]+", urls) if url.strip()]


def validate_urls(urls: str):
    url_list = split_urls(urls)
    validated = []

    for url in url_list:
        # 判断是否以指定前缀开头
        if url.startswith("https://www.youtube.com/"):
            validated.append(url)
        else:
            print(f"⚠️  跳过非 YouTube 地址: {url}")

    if len(validated) == 0:
        print("不存在 url")
        exit(1)

    return validated


def set_env(env: str | None):
    if env is None:
        return

    path = Path(env)
    if not path.exists():
        print(f"[ERROR] env={env} not exists!")

    load_dotenv(path)

    ffmpeg = os.getenv("FFmpeg", None)
    set_ffmpeg(ffmpeg)

    proxy = os.getenv("Proxy", None)
    set_proxy(proxy)


def set_ffmpeg(ffmpeg: str | None):
    """
    https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/postprocessor/ffmpeg.py#L102
    """
    global_options["ffmpeg"] = ffmpeg


def set_proxy(proxy: str | None):
    """
    https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L4163
    """
    global_options["proxy"] = proxy


def set_cookies(cookies: str | None):
    """
    https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L4179
    https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/cookies.py#L93
    """
    global_options["cookies"] = cookies


def set_js_runtime(js_runtime: str | None):
    """
    https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L853
    """
    if js_runtime is not None:
        global_options["js-runtime"] = {js_runtime: {}}


def get_videos_info(url_list: list[str]):
    options = {
        "proxy": global_options.get("proxy"),
        "cookiefile": global_options.get("cookies"),
        "js_runtimes": global_options.get("js-runtime"),
        "verbose": True,  # 输出详细日志
    }

    print(f"[get_videos_info] options={options}")

    video_info_list = []

    with yt_dlp.YoutubeDL(options) as downloader:  # type: ignore
        for url in url_list:
            # 提取信息（不下载）
            result = downloader.extract_info(url, download=False)
            if result is None:
                continue

            # 如果是播放列表
            if "entries" in result:
                # 添加所有视频
                video_info_list.extend(result["entries"])
            else:
                # 单个视频
                video_info_list.append(result)

    return video_info_list


def main(
    urls: str,
    env: Annotated[str | None, typer.Option(help="设置环境配置文件")] = None,
    folder: Annotated[str | None, typer.Option(help="视频下载路径")] = "videos",
    resolution: Annotated[int, typer.Option(help="视频分辨率")] = 1080,
    ffmpeg: Annotated[str | None, typer.Option(help="设置 ffmpeg 路径")] = None,
    proxy: Annotated[str | None, typer.Option(help="设置代理")] = None,
    cookies: Annotated[str | None, typer.Option(help="Cookie 文件路径")] = None,
    js_runtime: Annotated[
        str | None, typer.Option(help="JS 运行时: node/deno/bun/quickjs")
    ] = None,
):
    url_list = validate_urls(urls)

    set_env(env)
    set_ffmpeg(ffmpeg)
    set_proxy(proxy)
    set_cookies(cookies)
    set_js_runtime(js_runtime)

    print(f"url={url_list}")
    print(f"options={global_options}")

    video_info_list = get_videos_info(url_list)

    for info in video_info_list:
        print(f"[main] info={info}")


if __name__ == "__main__":
    typer.run(main)

# "https://www.youtube.com/watch?v=0xxrBVFNKeY"
# python downloader.py https://www.youtube.com/watch?v=0xxrBVFNKeY --proxy socks5://127.0.0.1:10808 --cookies "C:\Env\www.youtube.com_cookies.txt" --ffmpeg "C:\Env\ffmpeg-master-latest-win64-gpl\bin" --js_runtime node
