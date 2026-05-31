import os
import random

class SongSelector:
    song_playing = None
    song_playing_genre = None

    next_song= None
    next_song_genre = None

    directory = ""
    genres = [""]

    songs = []

    def __init__(self, directory='songs', genres=['rock', 'classical']):
        # Set directory and genres
        self.directory = directory
        self.genres = genres

        # List all songs with its genres
        for g in self.genres:
            genre_path = f"{self.directory}/{g}"
            if os.path.exists(genre_path):
                for dirpath, dirnames, filenames in os.walk(genre_path):
                    for filename in filenames:
                        # Only add actual audio files
                        if filename.endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac')):
                            full_path = os.path.join(dirpath, filename)
                            self.songs.append({"song": full_path, "genre": g})

        print(f"Songs found: {len(self.songs)}")
        print(f"Genres found: {len(self.genres)}")
        print(f"Directory: {self.directory}")

        # Select first song randomly (only if songs exist)
        if len(self.songs) > 0:
            rand_index = random.randint(0, len(self.songs)-1)
            self.next_song = self.songs[rand_index]["song"]
            self.next_song_genre = self.songs[rand_index]["genre"]
            self.set_playing_song()
        else:
            print(f"Warning: No songs found in {self.directory}")

    def set_playing_song(self):
        self.song_playing = self.next_song
        self.song_playing_genre = self.next_song_genre
                
    def choose_random_song_same_genre(self):
        # List all songs with the same genre
        same_genre_songs = []
        for s in self.songs:
            if s["genre"] == self.song_playing_genre and s["song"] != self.song_playing:
                same_genre_songs.append(s)

        # Choose a random song (only if songs of same genre exist)
        if len(same_genre_songs) > 0:
            rand_index = random.randint(0, len(same_genre_songs)-1)
            self.next_song = same_genre_songs[rand_index]["song"]
            self.next_song_genre = same_genre_songs[rand_index]["genre"]
        else:
            print(f"Warning: No other songs found in genre {self.song_playing_genre}")

    def choose_random_song_different_genre(self):
        # List all songs with a different genre
        different_genre_songs = []
        for s in self.songs:
            if s["genre"] != self.song_playing_genre:
                different_genre_songs.append(s)

        # Choose a random song (only if songs of different genre exist)
        if len(different_genre_songs) > 0:
            rand_index = random.randint(0, len(different_genre_songs)-1)
            self.next_song = different_genre_songs[rand_index]["song"]
            self.next_song_genre = different_genre_songs[rand_index]["genre"]
        else:
            print(f"Warning: No songs found in a different genre than {self.song_playing_genre}")