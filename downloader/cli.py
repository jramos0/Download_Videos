from __future__ import annotations

import argparse
from pathlib import Path

from .core import (
    ValidationError,
    convert_mp4_to_mp3,
    download_audio_as_mp3,
    download_video,
    download_video_to_mp3,
    read_urls_file,
    validate_urls,
)


def _add_url_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--url", action="append", default=[], help="Video URL. Repeat flag for multiple URLs.")
    parser.add_argument("--urls-file", type=Path, help="Path to text file with one URL per line.")


def _resolve_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = list(args.url)
    if args.urls_file:
        urls.extend(read_urls_file(args.urls_file))
    return validate_urls(urls)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="downloader",
        description="Download YouTube media and convert MP4 files to MP3.",
    )
    subparsers = parser.add_subparsers(dest="command")

    video = subparsers.add_parser("video", help="Download video(s) as MP4.")
    _add_url_inputs(video)
    video.add_argument("--output-dir", type=Path, default=Path("downloads/video"))
    video.add_argument(
        "--video-quality",
        default="1080p",
        help="Video quality: auto, 2k, fullhd, 1080p, 720p.",
    )
    video.add_argument("--verbose", action="store_true")

    audio = subparsers.add_parser("audio", help="Download audio as MP3.")
    _add_url_inputs(audio)
    audio.add_argument("--output-dir", type=Path, default=Path("downloads/audio"))
    audio.add_argument("--quality", type=int, default=192, choices=range(64, 321), metavar="64-320")
    audio.add_argument("--verbose", action="store_true")

    video_to_audio = subparsers.add_parser("video-to-audio", help="Download a video URL and convert to MP3.")
    _add_url_inputs(video_to_audio)
    video_to_audio.add_argument("--output-dir", type=Path, default=Path("downloads/video_to_audio"))
    video_to_audio.add_argument("--quality", type=int, default=192, choices=range(64, 321), metavar="64-320")
    video_to_audio.add_argument("--verbose", action="store_true")

    convert = subparsers.add_parser("convert", help="Convert local MP4 files to MP3.")
    convert.add_argument("--input-dir", type=Path, required=True)
    convert.add_argument("--overwrite", action="store_true", help="Overwrite existing MP3 files.")
    convert.add_argument("--recursive", action="store_true", help="Scan nested folders.")
    convert.add_argument("--bitrate", default="192k", help="Output MP3 bitrate (e.g. 128k, 192k, 320k).")

    subparsers.add_parser("menu", help="Open interactive console menu.")

    return parser


def _prompt(text: str, default: str | None = None) -> str:
    value = input(text).strip()
    if value:
        return value
    return default or ""


def _interactive_menu() -> int:
    print("=== Download Videos - Menu ===")
    print("1) Descargar video (MP4)")
    print("2) Descargar audio (MP3)")
    print("3) Convertir video URL a audio (MP3)")
    print("0) Salir")

    option = _prompt("Selecciona una opcion: ")
    if option == "0":
        print("Saliendo.")
        return 0

    if option not in {"1", "2", "3"}:
        print("Opcion invalida.")
        return 2

    def _video_quality_input() -> str:
        value = _prompt("Calidad de video [2k/fullhd/720p, default fullhd]: ", "fullhd").lower()
        if value not in {"2k", "fullhd", "720p", "1080p", "auto"}:
            raise ValidationError("La calidad de video debe ser: 2k, fullhd, 1080p, 720p o auto.")
        return value

    def _quality_input(prompt_text: str) -> int:
        value = _prompt(prompt_text, "192")
        try:
            quality = int(value)
        except ValueError as exc:
            raise ValidationError("La calidad debe ser un numero entre 64 y 320.") from exc
        if quality < 64 or quality > 320:
            raise ValidationError("La calidad debe estar entre 64 y 320.")
        return quality

    url = _prompt("Pega la URL: ")
    urls = validate_urls([url])

    if option == "1":
        output = Path(_prompt("Carpeta de salida [downloads/video]: ", "downloads/video"))
        video_quality = _video_quality_input()
        result = download_video(urls=urls, output_dir=output, video_quality=video_quality, verbose=False)
        print(f"Video download completed with exit code: {result}")
        return 0 if result == 0 else 1

    if option == "2":
        output = Path(_prompt("Carpeta de salida [downloads/audio]: ", "downloads/audio"))
        quality = _quality_input("Calidad MP3 64-320 [192]: ")
        result = download_audio_as_mp3(urls=urls, output_dir=output, quality_kbps=quality, verbose=False)
        print(f"Audio download completed with exit code: {result}")
        return 0 if result == 0 else 1

    output = Path(_prompt("Carpeta de salida [downloads/video_to_audio]: ", "downloads/video_to_audio"))
    quality = _quality_input("Calidad MP3 64-320 [192]: ")
    result = download_video_to_mp3(urls=urls, output_dir=output, quality_kbps=quality, verbose=False)
    print(f"Video-to-audio completed with exit code: {result}")
    return 0 if result == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command is None:
            return _interactive_menu()

        if args.command == "video":
            urls = _resolve_urls(args)
            result = download_video(
                urls=urls,
                output_dir=args.output_dir,
                video_quality=args.video_quality,
                verbose=args.verbose,
            )
            print(f"Video download completed with exit code: {result}")
            return 0 if result == 0 else 1

        if args.command == "audio":
            urls = _resolve_urls(args)
            result = download_audio_as_mp3(
                urls=urls,
                output_dir=args.output_dir,
                quality_kbps=args.quality,
                verbose=args.verbose,
            )
            print(f"Audio download completed with exit code: {result}")
            return 0 if result == 0 else 1

        if args.command == "video-to-audio":
            urls = _resolve_urls(args)
            result = download_video_to_mp3(
                urls=urls,
                output_dir=args.output_dir,
                quality_kbps=args.quality,
                verbose=args.verbose,
            )
            print(f"Video-to-audio completed with exit code: {result}")
            return 0 if result == 0 else 1

        if args.command == "convert":
            converted = convert_mp4_to_mp3(
                input_dir=args.input_dir,
                overwrite=args.overwrite,
                recursive=args.recursive,
                bitrate=args.bitrate,
            )
            print(f"Converted {converted} file(s) to MP3.")
            return 0

        if args.command == "menu":
            return _interactive_menu()

        parser.error("Unknown command")
        return 2

    except ValidationError as exc:
        print(f"Input error: {exc}")
        return 2
    except Exception as exc:
        print(f"Runtime error: {exc}")
        return 1
