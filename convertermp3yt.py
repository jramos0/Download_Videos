import yt_dlp

def download_audio_as_mp3(video_urls):
    try:
        # Configuration to download audio only and convert it to MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',  # Template for output filename
            'noplaylist': True,  # Only download a single video, not playlists
            'verbose': True  # Enable verbose output for debugging
        }

        for video_url in video_urls:
            print(f"Attempting to download audio from video: {video_url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.download([video_url])
                if result == 0:
                    print("Download and conversion to MP3 completed for:", video_url)
                else:
                    print("There was an issue during the download:", video_url)
                    
    except yt_dlp.utils.DownloadError as de:
        print(f"Download error: {de}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# List of YouTube URLs to download
video_urls = [
    "", #Put the links of the video
]

download_audio_as_mp3(video_urls)
