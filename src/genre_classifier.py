# Import libraries
import shutil
import librosa
import librosa.display
import IPython.display as ipd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from tqdm import tqdm
import pickle
import os
import scipy
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import tensorflow as tf
from tensorflow import keras
import requests
from zipfile import ZipFile
import pyaudio
import wave
import time
import tkinter as tk
from tkinter import filedialog
import asyncio
from threading import Thread

# local directory where script is being run
local_dir = os.getcwd()
print(f'El script se está ejecutando en el directorio: {local_dir}')

pickled_svcmodel = None

# Check file does not exist before downloading
if not os.path.exists('mytrain1.csv') or not os.path.exists('mytest1.csv'):
    shared_url = 'https://bit.ly/3STrPLY'

    # Set the path of the directory where you want to save the downloaded files
    local_path = './'

    # Download the ZIP file
    response = requests.get(shared_url)
    zip_file_path = os.path.join(local_path, 'ArchivesT1.zip')
    with open(zip_file_path, 'wb') as f:
        f.write(response.content)

    # Extract the ZIP file
    with ZipFile(zip_file_path, 'r') as zip:
        zip.extractall(local_path)

    # Delete the ZIP file
    os.remove(zip_file_path)

    print('Archivos descargados con éxito')

# Feature extraction function
def features_of_track(song_name_path):
    # Inicializo lista para features
    feature_row = []

    # Split filename and label
    filename = os.path.basename(song_name_path)
    label = os.path.splitext(filename)[0]

    column_names = ['filename', '#samples', 'chroma_cens_mean', 'chroma_cens_var',
                    'chroma_stft_mean', 'chroma_stft_var', 'spectral_centroid_mean', 'spectral_centroid_var',
                    'spectral_bandwidth_mean', 'spectral_bandwidth_var', 'spectral_contrast_mean',
                    'spectral_contrast_var', 'spectral_flatness_mean', 'spectral_flatness_var',
                    'zero_crossing_rate_mean', 'zero_crossing_rate_var', 'tonnetz_mean',
                    'tonnetz_var', 'rms_mean', 'rms_var', 'tempo',
                    'mfcc1_mean','mfcc1_var', 'mfcc2_mean','mfcc2_var',
                    'mfcc3_mean','mfcc3_var','mfcc4_mean', 'mfcc4_var',
                    'mfcc5_mean','mfcc5_var','mfcc6_mean','mfcc6_var',
                    'mfcc7_mean','mfcc7_var','mfcc8_mean','mfcc8_var',
                    'mfcc9_mean','mfcc9_var','mfcc10_mean','mfcc10_var',
                    'mfcc11_mean','mfcc11_var','mfcc12_mean','mfcc12_var',
                    'mfcc13_mean','mfcc13_var','label']

    try:
        # Load audio file
        y, sr = librosa.load(song_name_path)

        # Calculate the number of samples
        num_samples = len(y)

        # Extract features
        chroma_cens = librosa.feature.chroma_cens(y=y, sr=sr)
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        spectral_flatness = librosa.feature.spectral_flatness(y=y)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y=y)
        tonnetz = librosa.feature.tonnetz(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)
        #tempo = librosa.feature.rhythm.tempo(y=y, sr=sr)
        tempo = librosa.beat.tempo(y=y, sr=sr)
        MFCCs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

        # compute mean and var of features
        feature_row.extend([filename, num_samples,
                            np.mean(chroma_cens), np.var(chroma_cens),
                            np.mean(chroma_stft), np.var(chroma_stft),
                            np.mean(spectral_centroid), np.var(spectral_centroid),
                            np.mean(spectral_bandwidth), np.var(spectral_bandwidth),
                            np.mean(spectral_contrast), np.var(spectral_contrast),
                            np.mean(spectral_flatness), np.var(spectral_flatness),
                            np.mean(zero_crossing_rate), np.var(zero_crossing_rate),
                            np.mean(tonnetz), np.var(tonnetz),
                            np.mean(rms), np.var(rms),
                            tempo[0],
                            np.mean(MFCCs[0,:]),np.var(MFCCs[0,:]),
                            np.mean(MFCCs[1,:]),np.var(MFCCs[1,:]),
                            np.mean(MFCCs[2,:]),np.var(MFCCs[2,:]),
                            np.mean(MFCCs[3,:]),np.var(MFCCs[3,:]),
                            np.mean(MFCCs[4,:]),np.var(MFCCs[4,:]),
                            np.mean(MFCCs[5,:]),np.var(MFCCs[5,:]),
                           np.mean(MFCCs[6,:]),np.var(MFCCs[6,:]),
                           np.mean(MFCCs[7,:]),np.var(MFCCs[7,:]),
                           np.mean(MFCCs[8,:]),np.var(MFCCs[8,:]),
                           np.mean(MFCCs[9,:]),np.var(MFCCs[9,:]),
                           np.mean(MFCCs[10,:]),np.var(MFCCs[10,:]),
                           np.mean(MFCCs[11,:]),np.var(MFCCs[11,:]),
                           np.mean(MFCCs[12,:]),np.var(MFCCs[12,:]),label])

    except Exception as e:
        print(f'Error processing file {song_name_path}: {e}')
        return None, None  # Si error devuelve None

    return feature_row, column_names

# Load SVC model
with open('models/svcmodel1.pkl', 'rb') as f:
    pickled_svcmodel = pickle.load(f)

# Genre prediction function
TESTPATH = 'lib_test1'
def genrePredict_v2(trackspath = TESTPATH, onetrack=False, svc_model=None):
  """
  Realiza la predicción del género musical de las canciones
  contenidas en un directorio, y, también de una sóla canción
  haciendo onetrack= True
  """
  num_classical = 0
  # num_disco = 0
  num_rock = 0
  if not onetrack:
    for root, dirs, files in os.walk(trackspath):
      dirs.sort()
      for file in sorted(files):
        file_path = os.path.join(root, file)
        print(f'Computando features de track: {file} ')
        feat_val, _ = features_of_track(file_path)
        genero = pickled_svcmodel.predict([np.array(feat_val[2:-1], dtype=float)])
        print(f'Género: {genero} ')
        if (genero == 0):
          print('Classical')
          num_classical += 1
        #elif (genero == 1):
        #  print('Disco')
        #  num_disco += 1
        else:
          print('Rock')
          num_rock += 1
        print(f'---> Siguiente canción')
  else:
    print(f'Computando features de track: {trackspath} ')
    #filename = trackspath.split('/')[-1]
    feat_val, _ = features_of_track(trackspath)
    if svc_model is not None:
        genero = svc_model.predict([np.array(feat_val[2:-1], dtype=float)])
    else:
        genero = pickled_svcmodel.predict([np.array(feat_val[2:-1], dtype=float)])
    print(f'Género: {genero} ')
    if (genero == 0):
      num_classical += 1
      genre = 'Classical'
    #elif (genero == 1):
    #  print('Disco')
    #  num_disco += 1
    else:
      num_rock += 1
      genre = 'Rock'

  # return list([num_classical, num_disco, num_rock])
  return list([num_classical, num_rock]), genre

# Extract audio function
def getWav(filename="test.wav",
           tiempo=5,
           device_index=None,
           rate=44100,
           chunk=1024):

    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    # Borrar archivo previo si existe
    if os.path.exists(filename):
        os.remove(filename)

    p = pyaudio.PyAudio()

    try:
        # Buscar automáticamente un dispositivo de entrada
        if device_index is None:
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev["maxInputChannels"] > 0:
                    print(f"Usando dispositivo {i} - {dev['name']}")
                    device_index = i
                    break

        if device_index is None:
            print("No se encontró micrófono disponible")
            p.terminate()
            return False

        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk
        )

        print("Grabando...")

        frames = []

        for _ in range(int(rate / chunk * tiempo)):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)

        print("Grabación finalizada.")

        sample_width = p.get_sample_size(FORMAT)

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Guardar WAV
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(b"".join(frames))

        print(f"Archivo guardado en: {filename}")
        return True

    except Exception as e:
        print("ERROR durante la grabación:", e)
        p.terminate()
        return False

# Function to run async classify_music in a thread so it does not block the Tkinter mainloop
def classify_music(output_label, from_upload=False):
    def run_async():
        asyncio.run(classify_music_async(output_label, from_upload=from_upload))
    
    thread = Thread(target=run_async, daemon=True)
    thread.start()

def play_recorded_audio():
    def run_async():
        asyncio.run(play_recorded_audio_async())
    
    thread = Thread(target=run_async, daemon=True)
    thread.start()

# Play the recorded audio
async def play_recorded_audio_async():
    filename = 'test.wav'
    if not os.path.exists(filename):
        print("No se encontró el archivo test.wav para reproducir.")
        return
    try:
        wf = wave.open(filename, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        print(f"Error reproduciendo audio: {e}")

async def classify_music_async(output_label, from_upload=False):
    try:
        if not from_upload:
            print('grabando una canción')
            output_label.config(text="Grabando...")
        file='test.wav'
        model = 'svcmodel1.pkl'
        # 1. Borramos el archivo .wav para generar
        #    la siguiente predicción
        # Solo grabamos si no venimos de upload
        if not from_upload:
            os.remove(file) if os.path.exists(file) else None
            getWav(filename=file, tiempo=5)
        while not os.path.exists(file):
            await asyncio.sleep(0.1)

        print("Empezando clasificación...")
        if os.path.isfile(file):
        # 2. Ver si pickled_svc model está y
        #    si no, cargar el modelo
            print('cargando modelo...')
            if 'pickled_svcmodel' not in globals():
                pickled_svcmodel = pickle.load(open(model, 'rb'))

            # 3. Hacer genrePredict()
            #    y mostramos predicción por pantalla
            print('clasificando canción...')
            prediction, genre = genrePredict_v2(file, True)
            # Output label en Tkinter
            output_label.config(text=f"Género predicho: {genre}")
            print(f'predicción: {prediction}')     

        else:
            raise ValueError("%s wav no está!" % file)

    # el script termina con STOP en Jupyter,
    # (o con CTRL+C si run desde archivo)
    except KeyboardInterrupt:
        print('interrupted!')

def classify_music():
    try:
        # List files
        music_files = [f for f in os.listdir("unclassified_songs") if f.endswith('.wav')]

        # load model
        pickled_svcmodel = pickle.load(open('models/svcmodel1.pkl', 'rb'))
        print('Modelo cargado, clasificando canciones...')
        print(music_files)

        # Classify each file and move to corresponding genre folder
        for music_file in music_files:
            file_path = os.path.join("unclassified_songs", music_file)
            prediction, genre = genrePredict_v2(file_path, True, pickled_svcmodel)
            if (genre == 0):
                genre_folder = 'classical'
                print('Género predicho: Classical')
            else:
                genre_folder = 'rock'
                print('Género predicho: Rock')

            # Move file to corresponding genre folder
            dest_folder = os.path.join("songs", genre_folder)
            os.makedirs(dest_folder, exist_ok=True)
            shutil.move(file_path, os.path.join(dest_folder, music_file))

    except Exception as e:
        raise ValueError(f"Error al clasificar las canciones ({music_file}): {e}")