import os
from moviepy.editor import VideoFileClip

# Ruta a la carpeta que contiene los videos .mp4
folder_path = './why bitcoin/'

# Función para convertir .mp4 a .mp3
def convert_mp4_to_mp3(mp4_path, mp3_path):
    video = VideoFileClip(mp4_path)
    video.audio.write_audiofile(mp3_path)

# Iterar sobre todos los archivos en la carpeta
for filename in os.listdir(folder_path):
    if filename.endswith('.mp4'):
        mp4_path = os.path.join(folder_path, filename)
        mp3_path = os.path.join(folder_path, os.path.splitext(filename)[0] + '.mp3')
        convert_mp4_to_mp3(mp4_path, mp3_path)
        print(f'Convertido: {mp4_path} -> {mp3_path}')
