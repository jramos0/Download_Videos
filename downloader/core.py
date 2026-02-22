from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlsplit

import yt_dlp
from yt_dlp.utils import DownloadError


URL_RE = re.compile(r"^https?://")
YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}
HISTORY_FILE = Path("downloads/history.json")


class ValidationError(Exception):
    """Raised when user input is invalid."""


def _normalize_video_quality(video_quality: str) -> str:
    value = video_quality.strip().lower()
    aliases = {
        "auto": "auto",
        "best": "auto",
        "2k": "1440",
        "1440p": "1440",
        "fullhd": "1080",
        "fhd": "1080",
        "1080p": "1080",
        "hd": "720",
        "720p": "720",
    }
    if value not in aliases:
        raise ValidationError("Video quality must be one of: auto, 2k, fullhd, 1080p, 720p.")
    return aliases[value]


def _normalize_filename_style(filename_style: str) -> str:
    value = filename_style.strip().lower()
    aliases = {
        "clean": "clean",
        "clean-date": "clean-date",
        "date": "clean-date",
    }
    if value not in aliases:
        raise ValidationError("Filename style must be one of: clean, clean-date.")
    return aliases[value]


def _outtmpl_for_style(output_dir: Path, filename_style: str) -> str:
    style = _normalize_filename_style(filename_style)
    if style == "clean-date":
        template = "%(upload_date>%Y%m%d)s-%(title).180B.%(ext)s"
    else:
        template = "%(title).180B.%(ext)s"
    return str(output_dir / template)


def _video_format_for_quality(max_height: str) -> dict[str, str]:
    if max_height == "auto":
        return {
            "format": "bv*[ext=mp4][protocol!=m3u8]+ba[ext=m4a][protocol!=m3u8]/b[ext=mp4]/b",
        }
    return {
        "format": (
            f"bv*[ext=mp4][height<={max_height}][protocol!=m3u8]+"
            f"ba[ext=m4a][protocol!=m3u8]/"
            f"b[ext=mp4][height<={max_height}]/"
            f"b[height<={max_height}]"
        ),
    }


def _is_youtube_url(url: str) -> bool:
    parsed = urlsplit(url)
    host = parsed.netloc.lower()
    if host not in YOUTUBE_HOSTS:
        return False

    if host.endswith("youtu.be"):
        return bool(parsed.path.strip("/"))

    if parsed.path.startswith("/watch"):
        query = parse_qs(parsed.query)
        return bool(query.get("v"))

    return parsed.path.startswith(("/shorts/", "/live/", "/playlist"))


def validate_urls(urls: Iterable[str], youtube_only: bool = True) -> list[str]:
    cleaned = [u.strip() for u in urls if u and u.strip()]
    if not cleaned:
        raise ValidationError("No URLs were provided.")

    invalid = [u for u in cleaned if not URL_RE.match(u)]
    if invalid:
        raise ValidationError(f"Invalid URL(s): {', '.join(invalid)}")

    if youtube_only:
        non_youtube = [u for u in cleaned if not _is_youtube_url(u)]
        if non_youtube:
            raise ValidationError(
                "Only YouTube URLs are supported. Invalid URL(s): "
                f"{', '.join(non_youtube)}"
            )

    return cleaned


def read_urls_file(urls_file: Path) -> list[str]:
    if not urls_file.exists():
        raise ValidationError(f"URL file not found: {urls_file}")

    lines = [line.strip() for line in urls_file.read_text(encoding="utf-8").splitlines()]
    urls = [line for line in lines if line and not line.startswith("#")]
    return validate_urls(urls)


def ensure_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _read_history(history_file: Path = HISTORY_FILE) -> list[dict[str, Any]]:
    if not history_file.exists():
        return []

    try:
        data = json.loads(history_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []


def _append_history_entry(entry: dict[str, Any], history_file: Path = HISTORY_FILE) -> None:
    history_file.parent.mkdir(parents=True, exist_ok=True)
    history = _read_history(history_file)
    history.append(entry)
    history_file.write_text(json.dumps(history, indent=2, ensure_ascii=True), encoding="utf-8")


def _extract_output_path(info: dict[str, Any], force_ext: str | None = None) -> str | None:
    candidates: list[str] = []

    for key in ("filepath", "_filename"):
        value = info.get(key)
        if isinstance(value, str) and value:
            candidates.append(value)

    requested = info.get("requested_downloads")
    if isinstance(requested, list):
        for item in requested:
            if isinstance(item, dict):
                filepath = item.get("filepath")
                if isinstance(filepath, str) and filepath:
                    candidates.append(filepath)

    entries = info.get("entries")
    if isinstance(entries, list) and entries:
        first = entries[0]
        if isinstance(first, dict):
            nested = _extract_output_path(first, force_ext=force_ext)
            if nested:
                return nested

    if not candidates:
        return None

    output_path = Path(candidates[0])
    if force_ext:
        output_path = output_path.with_suffix(force_ext)
    return str(output_path)


def _build_history_entry(
    *,
    mode: str,
    url: str,
    status: str,
    output_dir: Path,
    info: dict[str, Any] | None,
    error: str | None,
    video_quality: str | None,
    audio_quality_kbps: int | None,
    filename_style: str,
    force_ext: str | None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "url": url,
        "status": status,
        "output_dir": str(output_dir),
        "filename_style": filename_style,
    }
    if video_quality is not None:
        entry["video_quality"] = video_quality
    if audio_quality_kbps is not None:
        entry["audio_quality_kbps"] = audio_quality_kbps
    if error:
        entry["error"] = error

    if info:
        if isinstance(info.get("id"), str):
            entry["video_id"] = info["id"]
        if isinstance(info.get("title"), str):
            entry["title"] = info["title"]
        output_path = _extract_output_path(info, force_ext=force_ext)
        if output_path:
            entry["output_file"] = output_path

    return entry


def _download_single_url_with_fallback(
    *,
    url: str,
    output_dir: Path,
    verbose: bool,
    profiles: list[dict[str, Any]],
    noplaylist: bool,
    merge_output_format: str | None,
    postprocessors: list[dict[str, Any]] | None,
    filename_style: str,
) -> dict[str, Any]:
    outtmpl = _outtmpl_for_style(output_dir, filename_style)
    last_exc: Exception | None = None

    for profile in profiles:
        ydl_opts: dict[str, Any] = {
            "outtmpl": outtmpl,
            "noplaylist": noplaylist,
            "quiet": not verbose,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            },
            **profile,
        }
        if merge_output_format:
            ydl_opts["merge_output_format"] = merge_output_format
        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            if isinstance(info, dict):
                return info
            return {}
        except DownloadError as exc:
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Download failed with no explicit error")


def download_audio_as_mp3(
    urls: list[str],
    output_dir: Path,
    quality_kbps: int = 192,
    verbose: bool = False,
    filename_style: str = "clean",
) -> int:
    ensure_output_dir(output_dir)
    style = _normalize_filename_style(filename_style)
    profiles = [
        {
            "format": "bestaudio[protocol!=m3u8]/bestaudio/best",
            "extractor_args": {"youtube": {"player_client": ["default"]}},
        },
        {
            "format": "bestaudio/best",
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        },
    ]

    for url in urls:
        try:
            info = _download_single_url_with_fallback(
                url=url,
                output_dir=output_dir,
                verbose=verbose,
                profiles=profiles,
                noplaylist=True,
                merge_output_format=None,
                postprocessors=[
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": str(quality_kbps),
                    }
                ],
                filename_style=style,
            )
            _append_history_entry(
                _build_history_entry(
                    mode="audio",
                    url=url,
                    status="success",
                    output_dir=output_dir,
                    info=info,
                    error=None,
                    video_quality=None,
                    audio_quality_kbps=quality_kbps,
                    filename_style=style,
                    force_ext=".mp3",
                )
            )
        except Exception as exc:
            _append_history_entry(
                _build_history_entry(
                    mode="audio",
                    url=url,
                    status="failed",
                    output_dir=output_dir,
                    info=None,
                    error=str(exc),
                    video_quality=None,
                    audio_quality_kbps=quality_kbps,
                    filename_style=style,
                    force_ext=".mp3",
                )
            )
            raise

    return 0


def download_video(
    urls: list[str],
    output_dir: Path,
    video_quality: str = "1080p",
    verbose: bool = False,
    filename_style: str = "clean",
) -> int:
    ensure_output_dir(output_dir)
    max_height = _normalize_video_quality(video_quality)
    style = _normalize_filename_style(filename_style)
    quality_format = _video_format_for_quality(max_height)

    profiles = [
        {
            **quality_format,
            "extractor_args": {"youtube": {"player_client": ["default"]}},
        },
        {
            "format": (
                "best[ext=mp4]/best"
                if max_height == "auto"
                else f"best[ext=mp4][height<={max_height}]/best[height<={max_height}]/best"
            ),
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        },
    ]

    for url in urls:
        try:
            info = _download_single_url_with_fallback(
                url=url,
                output_dir=output_dir,
                verbose=verbose,
                profiles=profiles,
                noplaylist=False,
                merge_output_format="mp4",
                postprocessors=None,
                filename_style=style,
            )
            _append_history_entry(
                _build_history_entry(
                    mode="video",
                    url=url,
                    status="success",
                    output_dir=output_dir,
                    info=info,
                    error=None,
                    video_quality=video_quality,
                    audio_quality_kbps=None,
                    filename_style=style,
                    force_ext=".mp4",
                )
            )
        except Exception as exc:
            _append_history_entry(
                _build_history_entry(
                    mode="video",
                    url=url,
                    status="failed",
                    output_dir=output_dir,
                    info=None,
                    error=str(exc),
                    video_quality=video_quality,
                    audio_quality_kbps=None,
                    filename_style=style,
                    force_ext=".mp4",
                )
            )
            raise

    return 0


def download_video_to_mp3(
    urls: list[str],
    output_dir: Path,
    quality_kbps: int = 192,
    verbose: bool = False,
    filename_style: str = "clean",
) -> int:
    """Download video media and extract it to MP3."""
    ensure_output_dir(output_dir)
    style = _normalize_filename_style(filename_style)
    profiles = [
        {
            "format": "bestaudio[protocol!=m3u8]/bestaudio/best",
            "extractor_args": {"youtube": {"player_client": ["default"]}},
        },
        {
            "format": "bestaudio/best",
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        },
    ]

    for url in urls:
        try:
            info = _download_single_url_with_fallback(
                url=url,
                output_dir=output_dir,
                verbose=verbose,
                profiles=profiles,
                noplaylist=True,
                merge_output_format=None,
                postprocessors=[
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": str(quality_kbps),
                    }
                ],
                filename_style=style,
            )
            _append_history_entry(
                _build_history_entry(
                    mode="video-to-audio",
                    url=url,
                    status="success",
                    output_dir=output_dir,
                    info=info,
                    error=None,
                    video_quality=None,
                    audio_quality_kbps=quality_kbps,
                    filename_style=style,
                    force_ext=".mp3",
                )
            )
        except Exception as exc:
            _append_history_entry(
                _build_history_entry(
                    mode="video-to-audio",
                    url=url,
                    status="failed",
                    output_dir=output_dir,
                    info=None,
                    error=str(exc),
                    video_quality=None,
                    audio_quality_kbps=quality_kbps,
                    filename_style=style,
                    force_ext=".mp3",
                )
            )
            raise

    return 0


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise ValidationError("ffmpeg is required but was not found in PATH.")


def convert_mp4_to_mp3(input_dir: Path, overwrite: bool = False, recursive: bool = False, bitrate: str = "192k") -> int:
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValidationError(f"Input directory not found: {input_dir}")

    require_ffmpeg()

    pattern = "**/*.mp4" if recursive else "*.mp4"
    mp4_files = sorted(input_dir.glob(pattern))
    if not mp4_files:
        raise ValidationError(f"No .mp4 files found in {input_dir}")

    converted = 0
    for mp4_file in mp4_files:
        mp3_file = mp4_file.with_suffix(".mp3")
        if mp3_file.exists() and not overwrite:
            continue

        cmd = [
            "ffmpeg",
            "-y" if overwrite else "-n",
            "-loglevel",
            "error",
            "-i",
            str(mp4_file),
            "-vn",
            "-acodec",
            "libmp3lame",
            "-ab",
            bitrate,
            str(mp3_file),
        ]
        subprocess.run(cmd, check=True)
        converted += 1

    return converted
