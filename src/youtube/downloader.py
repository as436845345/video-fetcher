import os  # 用于读取环境变量
import re  # 用于 URL 分割正则
from pathlib import Path  # 更安全的路径操作

import typer  # CLI 框架
import yt_dlp  # YouTube 下载工具
from dotenv import load_dotenv  # 加载 .env 文件
from typing_extensions import Annotated  # 用于参数注解

# 全局配置字典，用于存储 yt-dlp 相关参数
global_options = {}


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


def sanitize_string(string: str | None):
    """
    清理字符串，使其适合用于文件名或目录名。

    该函数会：
    1. 删除非法字符
    2. 仅保留：
        - 字母
        - 数字
        - 中文
        - 下划线 _
        - 连字符 -

    参数
    ----------
    string : str
        原始字符串（例如 YouTube 视频标题）

    返回
    ----------
    str
        清理后的安全字符串，可用于文件名
    """

    if string is None:
        return None

    # 删除除 字母/数字/中文/空格/_/- 以外的字符
    return re.sub(r"[^\w\u4e00-\u9fff\d_-]", "", string)


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


def set_env(env_file: str | None):
    """
    加载 .env 配置文件。

    支持配置:
        Proxy
    """

    if env_file is None:
        return  # 未指定 env 文件

    path = Path(env_file)

    if not path.exists():
        print(f"[ERROR] env={env_file} not exists!")

    # 加载 .env 文件
    load_dotenv(path)

    # 读取代理
    proxy = os.getenv("Proxy", None)
    set_proxy(proxy)


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

    # https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L853
    global_options["js-runtime"] = {js_runtime: {}}


def get_videos_info(url_list: list[str]):
    """
    获取视频 metadata（不下载）。

    返回：

        list[dict]

    每个 dict 是 yt-dlp 的 video info。
    """

    # yt-dlp 配置
    options = {
        # 代理
        "proxy": global_options.get("proxy"),
        # cookies
        "cookiefile": global_options.get("cookies"),
        # js runtime
        "js_runtimes": global_options.get("js-runtime"),
        # 详细日志
        "verbose": True,
    }

    # 存储所有视频信息
    video_info_list = []

    # 创建 yt-dlp 对象
    with yt_dlp.YoutubeDL(options) as downloader:  # type: ignore
        # 遍历 URL
        for url in url_list:
            # 提取视频信息（不下载）
            result = downloader.extract_info(url, download=False)

            # 如果失败
            if result is None:
                continue

            # 如果是播放列表
            if "entries" in result:
                # 添加所有视频
                video_info_list.extend(result["entries"])
            else:
                # 单个视频
                video_info_list.append(result)

    # 返回信息列表
    return video_info_list


def download_video(video_info: dict, output_dir: str | Path, resolution: int):
    """
    下载视频。

    参数
    ----------
    video_info
        yt-dlp 返回的视频信息

    output_dir
        下载目录

    resolution
        最大分辨率
    """

    # 清理标题
    title = sanitize_string(video_info["title"])
    # 清理 uploader 名称
    uploader = sanitize_string(video_info.get("uploader", "Unknown"))
    # 获取上传日期
    upload_date = video_info.get("upload_date", "Unknown")

    # 如果没有日期则跳过
    if upload_date == "Unknown":
        return

    # 构造输出目录
    output_folder = output_dir / uploader / f"{upload_date} {title}"  # type: ignore

    # 判断是否已经下载
    if os.path.exists(os.path.join(output_folder, "download.mp4")):
        print(f"Video already downloaded in {output_folder}")
        return

    # yt-dlp 下载配置
    options = {
        # 代理
        "proxy": global_options.get("proxy"),
        # cookies
        "cookiefile": global_options.get("cookies"),
        # js runtime
        "js_runtimes": global_options.get("js-runtime"),
        # 下载格式
        "format": f"bestvideo[ext=mp4][height<={resolution}]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        # 保存 metadata JSON
        "writeinfojson": global_options["save-info-json"],
        # 下载缩略图
        "writethumbnail": global_options["save-thumbnail"],
        # 输出模板
        "outtmpl": output_folder / global_options["output_name"],
        # 忽略错误
        "ignoreerrors": True,
        # 是否仅 metadata
        "skip_download": not global_options["metadata_only"],
        # 详细日志
        "verbose": True,
    }

    # 创建 yt-dlp
    with yt_dlp.YoutubeDL(options) as downloader:  # type: ignore
        # 下载视频
        downloader.download([video_info["webpage_url"]])

    print(f"Video downloaded in {output_folder}")


def main(
    urls: Annotated[
        str,
        typer.Argument(
            help="YouTube 视频或播放列表 URL，支持多个 URL（空格/逗号/换行分隔）"
        ),
    ],
    env_file: Annotated[
        str | None,
        typer.Option(
            "--env",
            help="加载 .env 配置文件（可包含 Proxy 等配置）",
        ),
    ] = None,
    output_dir: Annotated[
        str,
        typer.Option(
            "--output-dir",
            help="视频下载保存目录",
        ),
    ] = ".",
    output_name: Annotated[
        str,
        typer.Option(
            "--output-name",
            help="输出文件名模板（默认: download）",
        ),
    ] = "download",
    resolution: Annotated[
        int,
        typer.Option(
            "--resolution",
            help="最大视频分辨率，例如 720 / 1080 / 2160",
        ),
    ] = 1080,
    proxy: Annotated[
        str | None,
        typer.Option(
            "--proxy",
            help="HTTP/SOCKS 代理，例如 http://127.0.0.1:7890",
        ),
    ] = None,
    cookies: Annotated[
        str | None,
        typer.Option(
            "--cookies",
            help="cookies.txt 文件路径，用于访问会员或年龄限制视频",
        ),
    ] = None,
    js_runtime: Annotated[
        str,
        typer.Option(
            "--js-runtime",
            help="JavaScript runtime（node / deno / bun / quickjs）",
        ),
    ] = "node",
    save_info_json: Annotated[
        bool,
        typer.Option(
            "--save-info-json",
            help="保存 yt-dlp 提取的视频 metadata JSON",
        ),
    ] = False,
    save_thumbnail: Annotated[
        bool,
        typer.Option(
            "--save-thumbnail",
            help="下载视频缩略图",
        ),
    ] = False,
    metadata_only: Annotated[
        bool,
        typer.Option(
            "--metadata-only",
            help="仅获取视频信息，不下载视频",
        ),
    ] = False,
):
    """
    CLI 主函数。

    执行流程：

        1 验证 URL
        2 加载 env
        3 获取 metadata
        4 下载视频
    """

    # 验证 URL
    url_list = validate_urls(urls)

    # 加载 env
    set_env(env_file)

    # 写入配置
    global_options["output_name"] = output_name
    # 设置 proxy
    set_proxy(proxy)
    # 设置 cookies
    set_cookies(cookies)
    # 设置 js runtime
    set_js_runtime(js_runtime)
    # 保存 JSON
    global_options["save-info-json"] = save_info_json
    # 保存缩略图
    global_options["save-thumbnail"] = save_thumbnail
    # 只保存 metadata
    global_options["metadata_only"] = metadata_only

    # 获取视频信息
    video_info_list = get_videos_info(url_list)

    # 下载每个视频
    for video_info in video_info_list:
        download_video(video_info, output_dir, resolution)


# Python 入口
if __name__ == "__main__":

    # 启动 CLI
    typer.run(main)
