import yt_dlp

def download_audio_as_mp3(video_urls):
    try:
        # Configuración para descargar solo el audio y convertirlo a MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(title)s.%(ext)s',  
            'noplaylist': True,  
            'verbose': True 
        }

        for video_url in video_urls:
            print(f"Intentando descargar el audio del video: {video_url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.download([video_url])
                if result == 0:
                    print("Descarga y conversión a MP3 completada para:", video_url)
                else:
                    print("Hubo un problema durante la descarga:", video_url)
                    
    except yt_dlp.utils.DownloadError as de:
        print(f"Error durante la descarga: {de}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

# Lista de URLs de YouTube que deseas descargar
video_urls = [
    "https://youtu.be/VTqt8uaDa4o?si=o6j1ag5hOGNHl8PB",
   
]

download_audio_as_mp3(video_urls)
