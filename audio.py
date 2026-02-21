"""Compatibility wrapper for the unified downloader CLI (convert subcommand)."""

from __future__ import annotations

import sys

from downloader.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["convert", *sys.argv[1:]]))
