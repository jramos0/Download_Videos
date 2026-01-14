import os
from moviepy.editor import VideoFileClip

# Path to the folder containing .mp4 videos
folder_path = './Lightning Network/'

# Function to convert .mp4 to .mp3
def convert_mp4_to_mp3(mp4_path, mp3_path):
    video = VideoFileClip(mp4_path)
    video.audio.write_audiofile(mp3_path)

# Iterate over all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.mp4'):
        mp4_path = os.path.join(folder_path, filename)
        mp3_path = os.path.join(folder_path, os.path.splitext(filename)[0] + '.mp3')
        convert_mp4_to_mp3(mp4_path, mp3_path)
        print(f'Converted: {mp4_path} -> {mp3_path}')
