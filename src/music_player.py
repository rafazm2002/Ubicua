class MusicPlayer:

    def __init__(self):
        try:
            import pygame
        except ImportError as exc:
            raise ImportError("Instala pygame con: pip install pygame") from exc

        self.pygame = pygame
        self.pygame.mixer.init()
        self.song_path = None
        self.start_offset_s = 0.0

    def load(self, song_path):
        try:
            self.song_path = str(song_path)
            self.pygame.mixer.music.load(self.song_path)
        except Exception as exc:
            raise ValueError(f"Error al cargar la canción: {exc}") from exc

    def play(self, start_s=0.0):
        """Reproduce desde start_s segundos.

        Nota: en MP3, la precisión del salto puede depender de la codificación
        del archivo. Para pruebas docentes suele ser suficiente.
        """
        if self.song_path is None:
            raise ValueError("No se ha cargado ninguna canción")
        elif self.is_playing():
            raise RuntimeError("La canción ya se está reproduciendo")
        self.start_offset_s = float(start_s)
        self.pygame.mixer.music.play(start=self.start_offset_s)

    def is_playing(self):
        return self.pygame.mixer.music.get_busy()

    def get_time_s(self):
        """Devuelve el segundo aproximado dentro de la canción.

        pygame.get_pos() devuelve el tiempo transcurrido desde que empezó
        esta reproducción, por eso se suma start_offset_s.
        """
        pos_ms = self.pygame.mixer.music.get_pos()
        if pos_ms < 0:
            return self.start_offset_s
        return self.start_offset_s + pos_ms / 1000.0

    def stop(self):
        self.pygame.mixer.music.stop()