import pygame
import os
from moviepy.editor import AudioFileClip
import tkinter as tk
from pytube import YouTube, Playlist
import ctypes
import sys
from PIL import Image, ImageTk
import requests
from io import BytesIO

def run_as_admin():
    if sys.platform.startswith('win'):
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return
            else:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, sys.argv[0], None, 1)
                sys.exit(0)
        except Exception as e:
            print("Error:", e)

run_as_admin()

class AudioPlayerApp:
    def __init__(self, master):
        self.master = master
        master.title("Reproductor de Audio")

        self.master.configure(bg="#121212")  # Cambiar color de fondo
        self.master.option_add("*Font", "Helvetica 10")

        # Etiqueta para la URL
        self.label = tk.Label(master, text="URL del video de YouTube:", fg="white", bg="#121212")
        self.label.pack()

        # Entrada de texto para la URL
        self.url_entry = tk.Entry(master, bg="#212121", fg="white", insertbackground="white")
        self.url_entry.pack()
        
        # Botón para buscar la URL
        self.search_button = tk.Button(master, text="Buscar", command=self.search_url, bg="black", fg="white", relief="flat")
        self.search_button.pack()
        
        # Botones de navegación
        self.prev_button = tk.Button(master, text="⏮️", command=self.play_previous, bg="gray", fg="white", relief="flat", width=5)
        self.prev_button.pack()

        self.next_button = tk.Button(master, text="⏭️", command=self.play_next, bg="gray", fg="white", relief="flat", width=5)
        self.next_button.pack()

        # Etiqueta para el volumen
        self.volume_label = tk.Label(master, text="Volumen:", fg="white", bg="#121212")
        self.volume_label.pack()

        # Barra de volumen
        self.volume_scale = tk.Scale(master, from_=0, to=100, orient="horizontal", command=self.update_volume, bg="#121212", fg="white", highlightbackground="#121212", troughcolor="#1db954")
        self.volume_scale.pack()

        # Botón para iniciar la reproducción
        self.play_button = tk.Button(master, text="▶️", command=self.play_audio, bg="#1db954", fg="white", relief="flat", width=5)
        self.play_button.pack()

        # Botón para detener la reproducción
        self.stop_button = tk.Button(master, text="⏹️", command=self.stop_audio, bg="#d32f2f", fg="white", relief="flat", width=5)
        self.stop_button.pack()

        # Variable para controlar la reproducción
        self.playing = False
        self.index_selected = 0  # Índice de la canción actual en la lista de reproducción
        self.urls_videos = []  # Lista de URLs de los videos de la lista de reproducción
        self.playlist_url = "" # URL de la lista de reproducción de YouTube



        # Vincular la función update_volume al evento de cambio de la barra de volumen
        self.volume_scale.bind("<Motion>", self.update_volume)

        # Marco para la imagen de la portada
        self.image_frame = tk.Frame(master, bg="#121212")
        self.image_frame.pack()

        # Variable para almacenar la imagen de la portada
        self.cover_image = None

    def search_url(self):
        url = self.url_entry.get()
        if url:
            self.playlist_url = url  # Asigna la URL ingresada al atributo playlist_url
            
            # Obtener el índice de la URL
            index_start = url.find("index=")
            if index_start != -1:
                index_start += len("index=")
                index_end = url.find("&", index_start)
                if index_end == -1:
                    index_end = len(url)
                index_selected_str = url[index_start:index_end]
                try:
                    self.index_selected = int(index_selected_str) -1
                except ValueError:
                    print("Error: No se pudo convertir el índice a entero.")
                    return
                print(f"Índice seleccionado: {self.index_selected}")

            self.reproducir_lista(self.playlist_url)  # Obtener la lista de reproducción
            if not self.playing:
                self.descargar_y_reproducir_audio_youtube(url)


    def play_audio(self):
        if self.playing:
            pygame.mixer.music.pause()
            self.playing = False
            self.play_button.config(text="▶️")
        else:
            pygame.mixer.music.unpause()
            self.playing = True
            self.play_button.config(text="⏸️")
            # Mostrar la portada cuando se inicia la reproducción
            if self.cover_image:
                self.show_cover_image()

    def stop_audio(self):
        self.playing = False
        pygame.mixer.quit()

    def descargar_y_reproducir_audio_youtube(self, url):
        self.playing = True
        # Paso 1: Identificar el video con la URL
        yt = YouTube(url)

        # Obtener la URL de la imagen de la portada del video
        cover_url = yt.thumbnail_url

        # Obtener la imagen de la portada y mostrarla
        self.load_cover_image(cover_url)

        # Paso 2: Descargar el audio del video como archivo temporal
        stream = yt.streams.filter(only_audio=True).first()
        audio_filename = stream.download(filename="temp_audio")

       # Obtener la ruta absoluta del directorio actual
        current_directory = os.getcwd()
        audio_file_path = os.path.join(current_directory, "temp_audio.wav")

        # Paso 2.5: Convertir el archivo de audio a formato WAV (compatible con pygame)
        audio_clip = AudioFileClip(audio_filename)
        audio_clip.write_audiofile(audio_file_path, codec="pcm_s16le")
        audio_clip.close()

        # Eliminar el archivo de audio original
        try:
            os.remove(audio_filename)
        except Exception as e:
            print(f"Error al eliminar el archivo: {e}")

        # Paso 3: Reproducir el archivo de audio convertido
        pygame.mixer.init()
        pygame.mixer.music.load("./temp_audio.wav")
        pygame.mixer.music.set_volume(self.volume_scale.get() / 100)  # Configurar el volumen inicial
        pygame.mixer.music.play()

        # Esperar hasta que termine de reproducirse el audio
        self.check_audio_status()

    def check_audio_status(self):
        if not self.playing:
            return
        if pygame.mixer.music.get_busy():
            self.master.after(100, self.check_audio_status)  # Revisar cada 100 ms
        else:
            self.play_next()  # Reproducir la siguiente canción cuando termine

    def update_volume(self, event=None):
        if self.playing:
            pygame.mixer.music.set_volume(self.volume_scale.get() / 100)

    def obtener_urls_lista_reproduccion(self, playlist_url):
        try:
            playlist = Playlist(playlist_url)
            self.urls_videos = playlist.video_urls
            return self.urls_videos

        except Exception as e:
            print(f"Error al obtener las URLs de la lista de reproducción: {e}")
            return []

    def reproducir_lista(self, playlist_url):
        self.urls_videos = self.obtener_urls_lista_reproduccion(playlist_url)

        # Imprimir todas las URLs obtenidas
        print("URLs obtenidas de la lista de reproducción principal:")
        for url in self.urls_videos:
            print(url)

    def play_next(self):
        if not self.urls_videos:
            print("La lista de reproducción está vacía.")
            return

        # Detener la reproducción actual
        self.stop_audio()

        # Incrementar el índice para la siguiente canción
        self.index_selected += 1
        if self.index_selected >= len(self.urls_videos):
            self.index_selected = 0

        # Cambiar la pista que se está reproduciendo
        url_to_play = self.urls_videos[self.index_selected]
        self.descargar_y_reproducir_audio_youtube(url_to_play)


    def play_previous(self):
        if not self.urls_videos:
            print("La lista de reproducción está vacía.")
            return

        # Detener la reproducción actual
        self.stop_audio()

        # Disminuir el índice para la siguiente canción
        self.index_selected -= 1
        if self.index_selected < 0 :
            self.index_selected = int(len(self.urls_videos))

        # Cambiar la pista que se está reproduciendo
        url_to_play = self.urls_videos[self.index_selected]
        self.descargar_y_reproducir_audio_youtube(url_to_play)

    def load_cover_image(self, url):
        response = requests.get(url)
        img_data = response.content
        self.cover_image = Image.open(BytesIO(img_data))
        self.cover_image = self.cover_image.resize((200, 200), Image.LANCZOS)  # Cambiar a Image.LANCZOS
        self.cover_image = ImageTk.PhotoImage(self.cover_image)

    def show_cover_image(self):
        if self.cover_image:
            # Eliminar el widget Label anterior si ya existe
            for widget in self.image_frame.winfo_children():
                widget.destroy()

            # Mostrar la nueva imagen de la portada
            cover_label = tk.Label(self.image_frame, image=self.cover_image, bg="#121212")
            cover_label.image = self.cover_image
            cover_label.pack()


# Configuración de la ventana principal
root = tk.Tk()
app = AudioPlayerApp(root)
root.mainloop()
