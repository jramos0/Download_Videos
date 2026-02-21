from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

import yt_dlp
from yt_dlp.utils import DownloadError


URL_RE = re.compile(r"^https?://")


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


def validate_urls(urls: Iterable[str]) -> list[str]:
    cleaned = [u.strip() for u in urls if u and u.strip()]
    if not cleaned:
        raise ValidationError("No URLs were provided.")

    invalid = [u for u in cleaned if not URL_RE.match(u)]
    if invalid:
        raise ValidationError(f"Invalid URL(s): {', '.join(invalid)}")

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


def download_audio_as_mp3(urls: list[str], output_dir: Path, quality_kbps: int = 192, verbose: bool = False) -> int:
    ensure_output_dir(output_dir)
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
    last_exc: Exception | None = None
    for profile in profiles:
        ydl_opts = {
            "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": not verbose,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(quality_kbps),
                }
            ],
            **profile,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.download(urls)
        except DownloadError as exc:
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Audio download failed with no explicit error")


def download_video(
    urls: list[str],
    output_dir: Path,
    video_quality: str = "1080p",
    verbose: bool = False,
) -> int:
    ensure_output_dir(output_dir)
    max_height = _normalize_video_quality(video_quality)
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
    last_exc: Exception | None = None
    for profile in profiles:
        ydl_opts = {
            "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "noplaylist": False,
            "quiet": not verbose,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            },
            **profile,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.download(urls)
        except DownloadError as exc:
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Video download failed with no explicit error")


def download_video_to_mp3(urls: list[str], output_dir: Path, quality_kbps: int = 192, verbose: bool = False) -> int:
    """Download video media and extract it to MP3."""
    ensure_output_dir(output_dir)
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
    last_exc: Exception | None = None
    for profile in profiles:
        ydl_opts = {
            "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": not verbose,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(quality_kbps),
                }
            ],
            **profile,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.download(urls)
        except DownloadError as exc:
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Video-to-audio download failed with no explicit error")


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
