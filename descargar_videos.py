import os
import yt_dlp

# Define la lista de URLs de YouTube
urls = [
    #'https://www.youtube.com/watch?v=0ZgE-LjHWvI',
    #'https://www.youtube.com/watch?v=RaMeYgSBJQ0',
    'https://www.youtube.com/watch?v=Fy5W_ryWrCY',
    #'https://www.youtube.com/watch?v=a0Q_5dzpqKw',
    #'https://www.youtube.com/watch?v=BVYKeTXMtzQ',
    # Añade más URLs según sea necesario
]

# Define la carpeta de destino
output_folder = 'lightning'

# Crea la carpeta de destino si no existe
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def combine_video_audio(video_file, audio_file, output_file):
    if os.path.exists(video_file) and os.path.exists(audio_file):
        cmd = f"ffmpeg -y -loglevel error -i '{video_file}' -i '{audio_file}' -c copy -map 0:v:0 -map 1:a:0 -movflags +faststart '{output_file}'"
        os.system(cmd)
        print(f'Combinación completada: {output_file}')
    else:
        print(f'Error: Uno o ambos archivos no existen: {video_file}, {audio_file}')

def download_video(url):
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',  # Descargar el mejor video y audio en formatos específicos
            'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
            'verbose': True  # Habilitar salida detallada para depuración
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
            print(f'Video descargado y fusionado exitosamente: {url}')
    except Exception as e:
        print(f'Error al descargar {url}: {e}')

# Descarga y fusiona cada video en la lista de URLs
for url in urls:
    download_video(url)
