from src.music_player import MusicPlayer
from src.movement_analysis import calcula_frec_dom
from src.song_selector import SongSelector
from src.tempo_preprocessing import MusicProcesser
from src.genre_classifier import classify_music
import time


def compare_bpms(bpm_song, frec_dom, tolerance_percent=10):
    """
    Compara el BPM de la canción con la frecuencia dominante.
    
    Devuelve True si los BPMs son similares (dentro de la tolerancia),
    False si son diferentes.
    """
    if bpm_song is None or frec_dom is None:
        return True  # Si no tenemos datos, consideramos que son similares
    
    # Convertir frec_dom a BPM (si es necesario)
    # Asumimos que frec_dom está en Hz, multiplicamos por 60 para convertir a BPM
    frec_dom_bpm = frec_dom * 60
    
    # Calcular la diferencia porcentual
    if bpm_song == 0:
        return False
    
    diff_percent = abs(bpm_song - frec_dom_bpm) / bpm_song * 100
    
    return diff_percent <= tolerance_percent


def run_jukebox():
    # Classify music first
    classify_music()

    # Create song selector
    song_selector = SongSelector()

    # Create music player
    music_player = MusicPlayer()

    # Create music processer
    music_processer = MusicProcesser('songs')

    # Variables de control
    last_song_path = None
    last_bpm = None
    song_duration_s = None
    
    # Reproducir la primera canción
    song_path = song_selector.song_playing
    music_player.load(song_path)
    music_player.play()
    
    last_song_path = song_path

    # run loop
    while True:
        if music_player.is_playing():
            # Get current time in song
            current_time_s = music_player.get_time_s()

            # Process music to get tempo
            tempo = music_processer.get_tempo_at_time(song_path, current_time_s)

            # Analyze movement and get dominant frequency
            frec_dom = calcula_frec_dom(1)

            # Comparar BPMs para registrar el último BPM válido
            if tempo is not None:
                last_bpm = tempo

        else:
            # La canción ha terminado, reproducir la siguiente
            if last_song_path == song_path:  # Asegurarse de que la canción cambió
                # Comparar BPMs para decidir el género de la siguiente canción
                are_similar = compare_bpms(last_bpm, frec_dom)
                
                if are_similar:
                    # BPMs similares -> canción del mismo género
                    song_selector.choose_random_song_same_genre()
                else:
                    # BPMs diferentes -> canción de diferente género
                    song_selector.choose_random_song_different_genre()
                
                song_selector.set_playing_song()
                song_path = song_selector.song_playing
                
                # Cargar y reproducir la nueva canción
                music_player.load(song_path)
                music_player.play()
                
                last_song_path = song_path
                last_bpm = None
            else:
                # Pequeña pausa para no saturar CPU
                time.sleep(0.1)