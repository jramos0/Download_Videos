# Download Videos - Refactored CLI

Unified Python CLI for:
- Downloading YouTube videos as MP4
- Downloading YouTube audio as MP3
- Converting local `.mp4` files to `.mp3`
- Interactive menu mode to paste URLs directly

## Requirements

- Python 3.10+
- `ffmpeg` available in PATH

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Quick Start

Use the new unified CLI:

```bash
python3 -m downloader --help
```

## Interactive Menu (recommended)

Start the console menu:

```bash
python3 -m downloader
```

or:

```bash
python3 -m downloader menu
```

Menu options:
- `1` Download video (MP4), then paste URL
- `2` Download audio (MP3), then paste URL
- `3` Download video and convert to audio (MP3), then paste URL
- In option `1`, you can choose video quality: `2k`, `fullhd`, or `720p` (also accepts `1080p` and `auto`)

### 1) Download video(s) as MP4

Single URL:

```bash
python3 -m downloader video --url "https://www.youtube.com/watch?v=<id>"
```

Multiple URLs (repeat `--url`):

```bash
python3 -m downloader video \
  --url "https://www.youtube.com/watch?v=<id1>" \
  --url "https://www.youtube.com/watch?v=<id2>" \
  --video-quality fullhd \
  --output-dir downloads/video
```

From file (`urls.txt`, one URL per line, `#` comments allowed):

```bash
python3 -m downloader video --urls-file urls.txt --output-dir downloads/video
```

Quality options for `video`:
- `--video-quality 2k` (max 1440p)
- `--video-quality fullhd` (max 1080p)
- `--video-quality 720p` (max 720p)
- `--video-quality auto` (best available)

### 2) Download audio as MP3

```bash
python3 -m downloader audio \
  --url "https://www.youtube.com/watch?v=<id>" \
  --quality 192 \
  --output-dir downloads/audio
```

Or from file:

```bash
python3 -m downloader audio --urls-file urls.txt
```

### 3) Convert local MP4 files to MP3

```bash
python3 -m downloader convert --input-dir ./media
```

Recursive conversion and overwrite:

```bash
python3 -m downloader convert --input-dir ./media --recursive --overwrite --bitrate 320k
```

### 4) Download video URL and convert to MP3

```bash
python3 -m downloader video-to-audio --url "https://www.youtube.com/watch?v=<id>"
```

## Legacy scripts (still supported)

These wrappers now call the unified CLI:

- `download_videos.py` -> `video`
- `convertermp3yt.py` -> `audio`
- `audio.py` -> `convert`

Examples:

```bash
python3 download_videos.py --url "https://www.youtube.com/watch?v=<id>"
python3 convertermp3yt.py --url "https://www.youtube.com/watch?v=<id>"
python3 audio.py --input-dir ./media
```

## Testing

Run smoke tests:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Notes

- URL input is validated before download starts.
- Missing or invalid directories fail with explicit errors.
- Conversion uses `subprocess.run(..., check=True)` for reliable process failure handling.
