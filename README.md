# Jukebox Inteligente con Análisis de Movimiento

## Descripción General

Este es un jukebox interactivo que reproduce canciones y adapta automáticamente el género musical en función de los patrones de movimiento detectados por un sensor XBIMU (una pulsera sensor que mide el movimiento).

### ¿Cómo funciona?

1. **Reproducción de canciones**: El sistema comienza reproduciendo una canción aleatoria.

2. **Análisis de movimiento**: Mientras suena la canción, un sensor XBIMU conectado al puerto serial (COM6) captura los movimientos del usuario.

3. **Comparación de ritmos**: El sistema compara:
   - El **ritmo de la canción** (BPM - Beats Per Minute)
   - La **frecuencia de movimiento** detectada por el sensor

4. **Cambio de género**: Cuando termina la canción:
   - Si los ritmos son **similares** → la siguiente canción es del **mismo género**
   - Si los ritmos son **diferentes** → la siguiente canción es de un **género diferente**

---

## Estructura del Proyecto

```
Trabajo2/
├── main.py                          # Punto de entrada del programa
├── src/                             # Módulos principales
│   ├── genre_classifier.py          # Clasifica canciones en géneros
│   ├── jukebox_logic.py            # Lógica central del jukebox
│   ├── movement_analysis.py        # Análisis de movimiento desde XBIMU
│   ├── music_player.py             # Control de reproducción de audio
│   ├── song_selector.py            # Selección de canciones
│   ├── tempo_preprocessing.py      # Análisis de tempo/ritmo
│   └── utils.py                    # Funciones auxiliares
├── songs/                           # Librería de canciones
│   ├── classical/                  # Canciones de música clásica
│   └── rock/                       # Canciones de rock
├── models/                          # Modelos de clasificación (ML)
├── outputs/                         # Salida de análisis
├── tempo_jsons/                    # Archivos JSON con datos de tempo
├── lib_train1/ y lib_test1/       # Librerías de entrenamiento y prueba
└── unclassified_songs/            # Canciones sin clasificar
```

---

## Scripts en el Directorio `src/`

### 1. **main.py** - Punto de Entrada
**Ubicación**: Raíz del proyecto  
**Función**: Es el archivo que inicia todo el sistema. Llama a la función `run_jukebox()` para comenzar la reproducción.

```python
from src.jukebox_logic import run_jukebox
run_jukebox()
```

---

### 2. **jukebox_logic.py** - Lógica Principal del Sistema
**Responsabilidad**: Coordina todos los componentes y controla el flujo del jukebox.

**Funciones principales**:
- `compare_bpms(bpm_song, frec_dom, tolerance_percent)`: Compara el ritmo de la canción con la frecuencia de movimiento.
  - Convierte la frecuencia de movimiento a BPM (multiplicando por 60)
  - Calcula la diferencia porcentual entre ambos valores
  - Devuelve `True` si son similares (dentro de 10% por defecto), `False` si son diferentes

- `run_jukebox()`: Función principal que:
  1. Clasifica las canciones por género
  2. Selecciona la primera canción aleatoriamente
  3. Inicia la reproducción
  4. En un bucle infinito:
     - Obtiene el tempo actual de la canción
     - Analiza la frecuencia de movimiento del sensor
     - Cuando termina la canción, compara ritmos y elige el siguiente género

**Flujo**:
```
Clasificar canciones
    ↓
Seleccionar canción aleatoria
    ↓
Reproducir canción
    ↓
Mientras suena:
    - Analizar movimiento
    - Registrar tempo actual
    ↓
Canción termina:
    - ¿Ritmos similares?
      - SÍ → canción del mismo género
      - NO → canción de género diferente
    ↓
Repetir
```

---

### 3. **movement_analysis.py** - Análisis de Movimiento
**Responsabilidad**: Se comunica con el sensor XBIMU y analiza los movimientos del usuario.

**Hardware requerido**: 
- Sensor XBIMU conectado a puerto serial COM6
- Tasa de transmisión: 115200 baudios

**Función principal**:
- `calcula_frec_dom(num_calls)`: Calcula la frecuencia dominante del movimiento.
  1. Lee datos del sensor serial durante un tiempo determinado
  2. Almacena los datos en una cola (buffer)
  3. Aplica una transformada de Fourier (FFT) para obtener frecuencias
  4. Utiliza una ventana de Blackman para mejorar la precisión
  5. Devuelve la frecuencia dominante en Hz

**Parámetros**:
- `f_s = 64`: Frecuencia de muestreo (64 Hz)
- `maxlen = 256`: Tamaño del buffer de datos
- `samples_non_overlaped = 64`: Nuevas muestras entre análisis

---

### 4. **music_player.py** - Control de Reproducción de Audio
**Responsabilidad**: Controla la reproducción de canciones usando la librería pygame.

**Métodos principales**:
- `load(song_path)`: Carga un archivo de audio en memoria.
- `play(start_s=0.0)`: Comienza la reproducción desde un segundo específico.
- `is_playing()`: Devuelve `True` si hay una canción reproduciéndose.
- `get_time_s()`: Devuelve la posición actual en segundos de la canción.
- `stop()`: Detiene la reproducción.

**Librería utilizada**: Pygame mixer para reproducción de audio.

---

### 5. **song_selector.py** - Selección de Canciones
**Responsabilidad**: Gestiona la selección de canciones según el género.

**Atributos principales**:
- `songs`: Lista de todas las canciones encontradas con su género
- `song_playing`: La canción que se está reproduciendo actualmente
- `next_song`: La siguiente canción a reproducir
- `song_playing_genre`: Género de la canción actual

**Métodos principales**:
- `__init__(directory='songs', genres=['rock', 'classical'])`: Inicializa y busca todas las canciones en la carpeta.
- `choose_random_song_same_genre()`: Selecciona una canción aleatoria del mismo género.
- `choose_random_song_different_genre()`: Selecciona una canción aleatoria de un género diferente.
- `set_playing_song()`: Establece la siguiente canción como la canción actual.

**Extensión de géneros**: Es fácil agregar más géneros. Solo hay que crear nuevas carpetas en `songs/` con ese nombre y pasar la lista a la clase.

---

### 6. **tempo_preprocessing.py** - Análisis de Ritmo/Tempo
**Responsabilidad**: Analiza el tempo (ritmo) de las canciones en diferentes momentos.

**Conceptos principales**:
- **BPM (Beats Per Minute)**: Número de pulsaciones por minuto. Es el ritmo de la música.
- **Tempo Local**: El BPM puede variar a lo largo de la canción. Este módulo calcula el BPM en diferentes segmentos.

**Clase principal - `MusicProcesser`**:
- `__init__(music_folder)`: Inicializa con la carpeta de canciones.
- `analyze_song(song, genre)`: Analiza una canción y calcula su mapa de tempo.
- `load_or_analyze_song(song, genre)`: Carga el análisis desde un archivo JSON si existe, si no, lo calcula.
- `get_tempo_at_time(song_path, current_time_s)`: Devuelve el BPM en un momento específico de la canción.

**Proceso de análisis**:
1. Carga el archivo de audio
2. Detecta los "beats" (pulsos) de la música
3. Calcula el BPM global
4. Divide la canción en ventanas pequeñas (20 segundos)
5. Calcula el BPM en cada ventana
6. Suaviza los valores con mediana móvil
7. Detecta segmentos de tempo aproximadamente constante
8. Guarda todo en un archivo JSON en la carpeta `outputs/`

**Parámetros de análisis** (en `analyze_song`):
- `window_s=20`: Tamaño de cada ventana de análisis
- `hop_window_s=2.0`: Desplazamiento entre ventanas
- `smoothing_kernel=3`: Tamaño del kernel para suavizar
- `relative_change_threshold=0.1`: Cambio de 10% para detectar nuevo segmento
- `min_segment_s=10`: Duración mínima de un segmento

---

### 7. **genre_classifier.py** - Clasificación de Géneros
**Responsabilidad**: Clasifica automáticamente las canciones en géneros usando machine learning.

**Función principal**:
- `classify_music()`: Clasifica todas las canciones de la carpeta `unclassified_songs/` en géneros.

**Cómo funciona**:
1. Descarga un conjunto de datos de entrenamiento (si no existe)
2. Extrae características de audio de las canciones:
   - Chroma features (información de tonalidad)
   - Spectral centroid (brillo del audio)
   - Spectral bandwidth
   - Spectral contrast
   - Zero crossing rate (transiciones)
   - Tonnetz (espacio tonal)
   - RMS (energía)
   - MFCC (características perceptuales - 13 coeficientes)
   - Tempo (ritmo)

3. Entrena un modelo de Machine Learning (SVM)
4. Clasifica las canciones sin clasificar
5. Las mueve a la carpeta `songs/[género]/`

**Características extraídas**: Se utilizan 46 características diferentes de audio para hacer la clasificación.

---

### 8. **utils.py** - Funciones Auxiliares
**Estado**: Actualmente vacío. Se usa como placeholder para funciones auxiliares comunes que puedan necesitarse en el futuro.

---

## Flujo Completo del Programa

### Inicio
```
main.py
  ↓
run_jukebox() en jukebox_logic.py
```

### Clasificación Inicial
```
classify_music() en genre_classifier.py
  ├─ Descarga datos de entrenamiento
  ├─ Extrae características de las canciones sin clasificar
  ├─ Entrena modelo de ML
  └─ Clasifica y mueve canciones a sus carpetas
```

### Bucle Principal de Reproducción
```
SongSelector.choose_song() → Selecciona canción aleatoria
  ↓
MusicPlayer.load() → Carga la canción
  ↓
MusicPlayer.play() → Comienza reproducción
  ↓
BUCLE (mientras suena):
  ├─ MusicPlayer.get_time_s() → Obtiene tiempo actual
  ├─ MusicProcesser.get_tempo_at_time() → Obtiene BPM en ese momento
  ├─ movement_analysis.calcula_frec_dom() → Mide frecuencia de movimiento
  └─ Esperamos un poco y repetimos
  ↓
Cuando termina:
  ├─ jukebox_logic.compare_bpms() → Compara ritmos
  ├─ Si similares: SongSelector.choose_random_song_same_genre()
  ├─ Si diferentes: SongSelector.choose_random_song_different_genre()
  └─ Volvemos al paso "MusicPlayer.load()"
```

---

## Estructura de Datos Importantes

### Información de Canción (en SongSelector)
```python
{
    "song": "/ruta/a/cancion.mp3",
    "genre": "rock"  # o "classical"
}
```

### Mapa de Tempo (salida de MusicProcesser)
```json
{
    "song_id": "cancion_001",
    "global_bpm": 120.5,
    "duration_s": 240.0,
    "segments": [
        {
            "start_s": 0.0,
            "end_s": 20.5,
            "bpm": 118.3
        },
        {
            "start_s": 20.5,
            "end_s": 45.2,
            "bpm": 122.1
        }
    ]
}
```

---

## Dependencias Principales

- **pygame**: Reproducción de audio
- **librosa**: Análisis de características de audio
- **numpy**: Cálculos numéricos
- **scipy**: Procesamiento de señales (FFT, ventanas)
- **scikit-learn**: Machine Learning (SVM, escalado de datos)
- **tensorflow/keras**: Redes neuronales (si se utiliza)
- **pyaudio**: Interface de audio
- **requests**: Descargas de internet
- **pandas**: Manejo de datos
- **matplotlib/seaborn**: Visualización

---

## Configuración del Hardware

**Sensor XBIMU**:
- Puerto serial: `COM6`
- Velocidad: `115200` baudios
- Timeout: `15` segundos

El sensor envía datos en formato: `S,seq,valor_y,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,...`

Se utiliza el valor en la columna **2** (índice después de "S,seq") que corresponde a la aceleración en Y.

---

## Carpetas Importantes

### `songs/`
Librería organizada por género. Ejemplo:
```
songs/
  ├── rock/
  │   ├── cancion1.mp3
  │   ├── cancion2.wav
  │   └── ...
  └── classical/
      ├── sinfonia1.mp3
      ├── concierto.flac
      └── ...
```

### `outputs/`
Contiene los archivos JSON con el análisis de tempo de cada canción.
Ejemplo: `outputs/cancion_001_tempo_map.json`

### `unclassified_songs/`
Carpeta temporal donde se colocan las canciones nuevas para que el clasificador las analice y las mueva a `songs/[género]/`.

### `models/`
Almacena los modelos de Machine Learning entrenados para clasificación.

---

## Tolerancia de Comparación de Ritmos

Por defecto, la tolerancia es del **10%**. Esto significa:
- Si la canción tiene 120 BPM, el rango de movimiento similar es: 108-132 BPM
- Se puede ajustar el parámetro `tolerance_percent` en la función `compare_bpms()` en `jukebox_logic.py`

---

## Notas Técnicas

### ¿Por qué se multiplica por 60 la frecuencia?
En `jukebox_logic.py`:
```python
frec_dom_bpm = frec_dom * 60
```

Esto ocurre porque:
- El sensor mide **frecuencia en Hz** (ciclos por segundo)
- **BPM** es Beats Por **Minuto**
- Multiplicar por 60 convierte segundos a minutos: Hz → BPM

### Transformada de Fourier (FFT)
El análisis de movimiento utiliza FFT para convertir la señal temporal (movimiento en el tiempo) a su representación en frecuencia. Esto permite identificar la "frecuencia dominante" del movimiento, es decir, el ritmo principal con el que se mueve el usuario.

### Ventana de Blackman
Se aplica una ventana de Blackman antes de la FFT para reducir el "ruido espectral" y mejorar la precisión del análisis de frecuencia.

---

## Ejemplos de Uso

### Reproducción simple
```python
python main.py
```

### Análisis de una canción específica
```python
from src.tempo_preprocessing import analyze_audio_file_tempo
resultado = analyze_audio_file_tempo("songs/rock/mi_cancion.mp3")
print(f"BPM global: {resultado['global_bpm']}")
```

### Clasificar nuevas canciones
```python
from src.genre_classifier import classify_music
classify_music()
```

---

## Requisitos del Sistema

- **Python 3.7+**
- **Sensor XBIMU** conectado a COM6
- **Carpeta `songs/`** con subdirectorios para cada género
- **Conexión a Internet** (para descargar datos de entrenamiento la primera vez)

---

## Autor y Contexto

Este es un proyecto de la asignatura **Computación Ubicua (Ubicuos Computing)** del Máster.

El objetivo es demostrar cómo un sistema puede ser "sensible al contexto" (context-aware) usando:
- **Sensores** (XBIMU para movimiento)
- **Procesamiento de datos** (análisis de audio)
- **Machine Learning** (clasificación de géneros)
- **Adaptación dinámica** (cambio de música según contexto)

---

## Solución de Problemas

### "Cannot open serial port"
- Verificar que el sensor XBIMU está conectado a COM6
- Comprobar que no hay otra aplicación usando el puerto
- Cambiar el número de puerto en `movement_analysis.py` si es necesario

### "No songs found"
- Asegurarse de que la carpeta `songs/` existe
- Crear subcarpetas `songs/rock/` y `songs/classical/`
- Agregar archivos de audio en los formatos soportados (mp3, wav, flac, ogg, m4a, aac)

### Problema de clasificación de géneros
- Asegurarse de tener conexión a Internet para descargar datos
- Verificar que la carpeta `unclassified_songs/` existe
- Comprobar que los archivos de audio son válidos
# Ubicua
