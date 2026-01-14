import os
import yt_dlp

# Define the list of YouTube URLs
urls = [
    'https://www.youtube.com/watch?v=0ZgE-LjHWvI',
    'https://www.youtube.com/watch?v=RaMeYgSBJQ0',
    'https://www.youtube.com/watch?v=a0Q_5dzpqKw',
    # Add more URLs as needed
]

# Define the output folder
output_folder = ''

# Create the output folder if it does not exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def combine_video_audio(video_file, audio_file, output_file):
    if os.path.exists(video_file) and os.path.exists(audio_file):
        cmd = f"ffmpeg -y -loglevel error -i '{video_file}' -i '{audio_file}' -c copy -map 0:v:0 -map 1:a:0 -movflags +faststart '{output_file}'"
        os.system(cmd)
        print(f'Combination completed: {output_file}')
    else:
        print(f'Error: One or both files do not exist: {video_file}, {audio_file}')

def download_video(url):
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',  # Download the best video and audio in specific formats
            'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
            'verbose': True  # Enable verbose output for debugging
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', None)
            video_ext = info_dict['requested_formats'][0]['ext']
            audio_ext = info_dict['requested_formats'][1]['ext']
            video_file = os.path.join(output_folder, f"{video_title}.{video_ext}")
            audio_file = os.path.join(output_folder, f"{video_title}.{audio_ext}")
            output_file = os.path.join(output_folder, f"{video_title}.mp4")
            combine_video_audio(video_file, audio_file, output_file)
            print(f'Video downloaded and merged successfully: {url}')
    except Exception as e:
        print(f'Error downloading {url}: {e}')

# Download and merge each video in the URL list
for url in urls:
    download_video(url)
