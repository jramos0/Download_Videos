"""Compatibility wrapper for the unified downloader CLI (video subcommand)."""

from __future__ import annotations

import sys

from downloader.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["video", *sys.argv[1:]]))
