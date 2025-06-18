from base_manager import BaseManager

class PlaylistSongManager(BaseManager):
    def __init__(self, db_manager):
        # Definición de columnas de la tabla playlist_cancion
        # Asegúrate de que estas columnas coincidan con tu esquema de base de datos
        columns = {
            "id_playlist": "INT",
            "id_cancion": "INT",
            "orden": "INT"
        }
        # ¡IMPORTANTE! Hemos cambiado "playlist_song" a "playlist_cancion" aquí
        super().__init__(db_manager, "playlist_cancion", columns, "id_playlist")

