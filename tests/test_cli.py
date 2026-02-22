from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from downloader.cli import main
from downloader.core import download_video


class CLISmokeTests(unittest.TestCase):
    def test_video_requires_url(self) -> None:
        code = main(["video"])
        self.assertEqual(code, 2)

    def test_audio_invalid_url(self) -> None:
        code = main(["audio", "--url", "not-a-url"])
        self.assertEqual(code, 2)

    def test_non_youtube_url_is_rejected(self) -> None:
        code = main(["video", "--url", "https://vimeo.com/123"])
        self.assertEqual(code, 2)

    @patch("downloader.cli.download_video", return_value=0)
    def test_video_quality_argument_is_forwarded(self, mock_download_video) -> None:
        code = main(
            [
                "video",
                "--url",
                "https://www.youtube.com/watch?v=abc123",
                "--video-quality",
                "720p",
                "--filename-style",
                "clean-date",
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(mock_download_video.call_args.kwargs["video_quality"], "720p")
        self.assertEqual(mock_download_video.call_args.kwargs["filename_style"], "clean-date")

    @patch("downloader.core.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("downloader.core.subprocess.run")
    def test_convert_runs_ffmpeg(self, mock_run, _mock_which) -> None:
        mock_run.return_value = subprocess.CompletedProcess(args=["ffmpeg"], returncode=0)
        with tempfile.TemporaryDirectory() as tmp_dir:
            mp4 = Path(tmp_dir) / "clip.mp4"
            mp4.write_bytes(b"fake")
            code = main(["convert", "--input-dir", tmp_dir])

        self.assertEqual(code, 0)
        self.assertTrue(mock_run.called)

    @patch("downloader.core.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("downloader.core.subprocess.run")
    def test_convert_skips_existing_without_overwrite(self, mock_run, _mock_which) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            (base / "clip.mp4").write_bytes(b"fake")
            (base / "clip.mp3").write_bytes(b"existing")
            code = main(["convert", "--input-dir", tmp_dir])

        self.assertEqual(code, 0)
        mock_run.assert_not_called()

    @patch("downloader.cli.download_video", return_value=0)
    @patch("builtins.input", side_effect=["1", "https://www.youtube.com/watch?v=abc123", "", "720p", "clean-date", "0"])
    def test_menu_option_1(self, _mock_input, mock_download_video) -> None:
        code = main(["menu"])
        self.assertEqual(code, 0)
        self.assertTrue(mock_download_video.called)
        self.assertEqual(mock_download_video.call_args.kwargs["video_quality"], "720p")
        self.assertEqual(mock_download_video.call_args.kwargs["filename_style"], "clean-date")

    @patch("downloader.core._download_single_url_with_fallback", return_value={"id": "abc123", "title": "Demo", "_filename": "downloads/video/demo.webm"})
    @patch("downloader.core._append_history_entry")
    def test_history_is_written_for_video_success(self, mock_append_history, _mock_download) -> None:
        code = download_video(
            urls=["https://www.youtube.com/watch?v=abc123"],
            output_dir=Path("downloads/video"),
            video_quality="720p",
            filename_style="clean",
            verbose=False,
        )
        self.assertEqual(code, 0)
        self.assertEqual(mock_append_history.call_count, 1)
        entry = mock_append_history.call_args.args[0]
        self.assertEqual(entry["mode"], "video")
        self.assertEqual(entry["status"], "success")
        self.assertTrue(entry["output_file"].endswith(".mp4"))


if __name__ == "__main__":
    unittest.main()
