"""Compatibility wrapper for the unified downloader CLI (audio subcommand)."""

from __future__ import annotations

import sys

from downloader.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["audio", *sys.argv[1:]]))
