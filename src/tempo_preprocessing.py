"""
tempo_preprocessing.py

Módulo de apoyo para la Tarea 4: creación de un mapa temporal de tempo
para UN archivo de audio.

La función principal que se pide en esta tarea es:

    analyze_audio_file_tempo("music/cancion_001.mp3")

Esta función devuelve un diccionario con el BPM global de la canción, una
lista de segmentos de tempo aproximadamente constante y una pista local de BPM
para visualizar el proceso. El JSON final se guarda en formato compacto.
"""

from pathlib import Path
import json
import math
import numpy as np
import librosa

AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
MUSIC_DIR = Path("music")

MUSIC_DIR.mkdir(exist_ok=True)

music_files = sorted(
    p for p in MUSIC_DIR.iterdir()
    if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
)

print("Archivos de audio encontrados:")
for p in music_files:
    print(" -", p.name)


def is_number(x):
    """Devuelve True si x es un número finito."""
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def valid_bpm(x, min_bpm, max_bpm):
    """
    Comprueba si un BPM está dentro de un rango razonable para música.

    Devuelve True si x es un número finito y está entre min_bpm y max_bpm.
    Devuelve False en caso contrario.

    min_bpm y max_bpm no se fijan aquí para evitar que el mismo criterio
    aparezca definido en varios lugares. Esos valores se configuran desde
    analyze_audio_file_tempo() y se pasan como argumentos a esta función.
    """
    return is_number(x) and min_bpm <= float(x) <= max_bpm


def _to_float_tempo(tempo):
    """
    Convierte a float la salida de librosa.beat.beat_track.

    Según la versión de librosa y el tipo de entrada, el tempo puede venir como
    un escalar, una lista o un array de NumPy. Esta función normaliza esa salida
    para que el resto del código trabaje siempre con un único valor float.
    Si no hay ningún valor de tempo disponible, devuelve None.
    """
    arr = np.asarray(tempo).reshape(-1)
    if arr.size == 0:
        return None
    return float(arr[0])


def load_audio(audio_path, sr):
    """
    Carga un archivo de audio con librosa.

    El audio se carga en mono (`mono=True`) porque, para estimar tempo y beats,
    no necesitamos conservar la separación estéreo. Una única señal temporal
    simplifica el análisis y reduce el coste computacional.

    Parámetros
    ----------
    audio_path : str o pathlib.Path
        Ruta del archivo de audio. librosa puede cargar WAV y, en muchos
        entornos, también MP3 y otros formatos habituales.

    sr : int o None
        Frecuencia de muestreo a la que librosa cargará o remuestreará el audio.
        En esta tarea se propone 22050 Hz desde analyze_audio_file_tempo(),
        porque es un valor habitual en análisis musical: reduce el coste
        computacional y mantiene información suficiente para estimar tempo y
        beats. Si se usa sr=None, librosa conserva la frecuencia de muestreo
        original del archivo.

    Devuelve
    --------
    y : numpy.ndarray
        Señal de audio mono.
    sr_out : int
        Frecuencia de muestreo de la señal devuelta.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {audio_path}")

    y, sr_out = librosa.load(str(audio_path), sr=sr, mono=True)
    return y, sr_out


def estimate_bpm_from_signal(y, sr, min_bpm, max_bpm, min_beats):
    """
    Estima el BPM de una señal de audio ya cargada usando librosa.

    La función calcula la envolvente de onsets y usa librosa.beat.beat_track
    para estimar el tempo y localizar beats. Los criterios min_bpm, max_bpm y
    min_beats se reciben desde la función principal para mantener centralizada
    la configuración de la tarea.
    """
    if y is None or len(y) == 0:
        return {"bpm": None, "n_beats": 0, "reason": "empty_signal"}

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    if onset_env is None or len(onset_env) == 0 or float(np.max(onset_env)) <= 0:
        return {"bpm": None, "n_beats": 0, "reason": "no_onsets"}

    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, trim=False)
    tempo = _to_float_tempo(tempo)
    n_beats = int(len(beats))

    if tempo is None or not valid_bpm(tempo, min_bpm, max_bpm):
        return {"bpm": None, "n_beats": n_beats, "reason": "tempo_out_of_range"}

    if n_beats < min_beats:
        return {"bpm": None, "n_beats": n_beats, "reason": "not_enough_beats"}

    return {
        "bpm": float(tempo),
        "n_beats": n_beats,
        "reason": "ok",
    }


def estimate_global_bpm(audio_path, sr, min_bpm, max_bpm, min_beats):
    """Estima el BPM global de un archivo de audio usando librosa."""
    y, sr_out = load_audio(audio_path, sr)
    result = estimate_bpm_from_signal(y, sr_out, min_bpm, max_bpm, min_beats)
    result["duration_s"] = float(len(y)) / float(sr_out)
    return result


def estimate_local_bpm_track(
    audio_path,
    window_s,
    hop_window_s,
    sr,
    min_bpm,
    max_bpm,
    min_beats,
    min_window_s,
):
    """
    Calcula una serie temporal de BPM locales mediante ventanas deslizantes.

    Los parámetros se reciben desde analyze_audio_file_tempo(), que actúa como
    punto único de configuración.
    """
    y, sr_out = load_audio(audio_path, sr)
    duration_s = float(len(y)) / float(sr_out)

    track = []
    start = 0.0
    while start < duration_s:
        end = min(start + float(window_s), duration_s)
        if end - start < float(min_window_s):
            break

        start_sample = int(round(start * sr_out))
        end_sample = int(round(end * sr_out))
        y_win = y[start_sample:end_sample]

        result = estimate_bpm_from_signal(
            y_win,
            sr_out,
            min_bpm,
            max_bpm,
            min_beats,
        )

        track.append({
            "start_s": round(float(start), 3),
            "end_s": round(float(end), 3),
            "center_s": round(float((start + end) / 2.0), 3),
            "bpm": None if result["bpm"] is None else round(float(result["bpm"]), 3),
            "n_beats": int(result.get("n_beats", 0)),
            "reason": result.get("reason", ""),
        })

        start += float(hop_window_s)

    return track, duration_s


def median_smooth(values, kernel_size):
    """
    Suaviza una lista con mediana móvil.
    """
    if kernel_size <= 1:
        return values[:]

    half = int(kernel_size) // 2
    smoothed = []

    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        window = [v for v in values[lo:hi] if v is not None and is_number(v)]

        if window:
            smoothed.append(float(np.median(window)))
        else:
            smoothed.append(None)

    return smoothed


def detect_tempo_segments(
    local_track,
    duration_s,
    global_bpm,
    smoothing_kernel,
    relative_change_threshold,
    min_segment_s,
    min_bpm,
    max_bpm,
):
    """
    Detecta segmentos de tempo aproximadamente constante.

    Esta función contiene una estrategia base de segmentación. En la tarea no es
    necesario modificar su lógica interna: lo habitual será estudiar cómo cambian
    los resultados al variar, desde analyze_audio_file_tempo(), parámetros como
    smoothing_kernel, relative_change_threshold o min_segment_s. Si se modifica
    esta función, debe justificarse claramente.
    """
    if not local_track:
        return [{
            "start_s": 0.0,
            "end_s": round(float(duration_s), 3),
            "bpm": None if global_bpm is None else round(float(global_bpm), 3)
        }], []

    raw_bpms = [row.get("bpm") for row in local_track]
    smooth_bpms = median_smooth(raw_bpms, smoothing_kernel)

    enriched_track = []
    for row, smooth in zip(local_track, smooth_bpms):
        new_row = dict(row)
        new_row["bpm_smooth"] = None if smooth is None else round(float(smooth), 3)
        enriched_track.append(new_row)

    valid_points = [
        (row["center_s"], row["bpm_smooth"])
        for row in enriched_track
        if row["bpm_smooth"] is not None and valid_bpm(row["bpm_smooth"], min_bpm, max_bpm)
    ]

    if not valid_points:
        return [{
            "start_s": 0.0,
            "end_s": round(float(duration_s), 3),
            "bpm": None if global_bpm is None else round(float(global_bpm), 3)
        }], enriched_track

    segments = []
    current_start = 0.0
    current_values = [valid_points[0][1]]
    current_ref = float(valid_points[0][1])

    for t, bpm in valid_points[1:]:
        bpm = float(bpm)
        rel_change = abs(bpm - current_ref) / current_ref

        if rel_change >= relative_change_threshold and (float(t) - current_start) >= min_segment_s:
            segment_bpm = float(np.median(current_values))
            segments.append({
                "start_s": round(float(current_start), 3),
                "end_s": round(float(t), 3),
                "bpm": round(segment_bpm, 3)
            })
            current_start = float(t)
            current_values = [bpm]
            current_ref = bpm
        else:
            current_values.append(bpm)
            current_ref = float(np.median(current_values))

    segments.append({
        "start_s": round(float(current_start), 3),
        "end_s": round(float(duration_s), 3),
        "bpm": round(float(np.median(current_values)), 3)
    })

    return segments, enriched_track


def analyze_audio_file_tempo(
    audio_path,
    song_id=None,
    title=None,
    window_s=20,
    hop_window_s=5,
    smoothing_kernel=3,
    relative_change_threshold=0.12,
    min_segment_s=10,
    min_bpm=40,
    max_bpm=220,
    min_beats=2,
    min_window_s=6,
    sr=22050,
):
    """
    Analiza UN archivo de audio y devuelve su mapa temporal de tempo.

    Esta función actúa como punto principal de configuración. Para estudiar el
    comportamiento del algoritmo, modificad aquí los parámetros de ventana,
    suavizado, umbral de cambio, duración mínima de segmento y rango válido de
    BPM, en lugar de cambiar valores dispersos en las funciones auxiliares.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {audio_path}")

    if song_id is None:
        song_id = audio_path.stem
    if title is None:
        title = audio_path.stem

    global_result = estimate_global_bpm(
        audio_path,
        sr,
        min_bpm,
        max_bpm,
        min_beats,
    )
    duration_s = float(global_result.get("duration_s", 0.0))

    local_track, duration_s = estimate_local_bpm_track(
        audio_path,
        window_s,
        hop_window_s,
        sr,
        min_bpm,
        max_bpm,
        min_beats,
        min_window_s,
    )

    segments, enriched_track = detect_tempo_segments(
        local_track,
        duration_s,
        global_result["bpm"],
        smoothing_kernel,
        relative_change_threshold,
        min_segment_s,
        min_bpm,
        max_bpm,
    )

    tempo_mode = "constant" if len(segments) == 1 else "segmented"

    return {
        "song_id": str(song_id),
        "title": str(title),
        "file": str(audio_path),
        "duration_s": round(float(duration_s), 3),
        "global_bpm": None if global_result["bpm"] is None else round(float(global_result["bpm"]), 3),
        "tempo_mode": tempo_mode,
        "segments": segments,
        # Información auxiliar para visualizar y depurar en el notebook.
        # No se guarda en el JSON final.
        "local_bpm_track": enriched_track,
    }


def compact_tempo_map(song_tempo_map):
    """
    Devuelve la versión compacta del mapa de tempo que se guardará en JSON.

    El JSON final solo debe contener los datos necesarios para usar el mapa en
    el Proyecto 2: identificador/título, archivo, duración, BPM global y segmentos.
    No se incluyen parámetros de configuración ni la serie local de BPM por ventanas.
    """
    compact_segments = []
    for seg in song_tempo_map.get("segments", []):
        compact_segments.append({
            "start_s": seg.get("start_s"),
            "end_s": seg.get("end_s"),
            "bpm": seg.get("bpm"),
        })

    return {
        "song_id": song_tempo_map.get("song_id"),
        "title": song_tempo_map.get("title", song_tempo_map.get("song_id")),
        "file": song_tempo_map.get("file"),
        "duration_s": song_tempo_map.get("duration_s"),
        "global_bpm": song_tempo_map.get("global_bpm"),
        "tempo_mode": song_tempo_map.get("tempo_mode"),
        "segments": compact_segments,
    }


def save_tempo_map(song_tempo_map, output_json):
    """Guarda en JSON la versión compacta del mapa temporal de una canción."""
    output_json = Path(output_json)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(compact_tempo_map(song_tempo_map), f, indent=2, ensure_ascii=False)
    return output_json

class MusicProcesser:
    mussic_folder = None
    tempo_maps = {}  # Cache para almacenar mapas de tempo de las canciones

    def __init__(self, music_folder):
        self.mussic_folder = music_folder

    def analyze_song(self, song, genre):
        song_path = f"{self.mussic_folder}/{genre}/{song}"
        song_tempo_map = analyze_audio_file_tempo(
            song_path,
            window_s=20,
            hop_window_s=2.0,
            smoothing_kernel=3,
            relative_change_threshold=0.1,
            min_segment_s=10,
        )

        return song_tempo_map
    
    def create_json(song_tempo_map):
        save_tempo_map(song_tempo_map, Path(f"outputs/{song_tempo_map.get('song_id', 'unknown')}_tempo_map.json"))
        return
    
    def load_or_analyze_song(self, song, genre):
        """Carga el mapa de tempo de una canción desde JSON o lo analiza si no existe."""
        json_path = Path(f"outputs/{song}_tempo_map.json")
        
        if json_path.exists():
            with open(json_path, "r") as f:
                return json.load(f)
        else:
            return self.analyze_song(song, genre)
    
    def get_tempo_at_time(self, song_path, current_time_s):
        """Devuelve el BPM en un tiempo específico de la canción."""
        # Extraer el nombre de la canción del path
        song_name = Path(song_path).stem
        
        # Si no tenemos el mapa de tempo cargado, intentamos cargarlo
        if song_name not in self.tempo_maps:
            try:
                json_path = Path(f"outputs/{song_name}_tempo_map.json")
                if json_path.exists():
                    with open(json_path, "r") as f:
                        self.tempo_maps[song_name] = json.load(f)
                else:
                    return None
            except Exception:
                return None
        
        tempo_map = self.tempo_maps[song_name]
        
        # Buscar el segmento que contiene el tiempo actual
        for segment in tempo_map.get("segments", []):
            if segment["start_s"] <= current_time_s <= segment["end_s"]:
                return segment.get("bpm")
        
        # Si no encontramos un segmento, devolvemos el BPM global
        return tempo_map.get("global_bpm")
