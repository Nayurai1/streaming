from base_manager import BaseManager

class SongManager(BaseManager):
    """
    Clase para gestionar la tabla 'cancion'.
    Hereda la funcionalidad CRUD básica de BaseManager.
    """
    def __init__(self, db_manager):
        columns = {
            "id_cancion": "INT",
            "titulo_cancion": "TEXT",
            "duracion": "TIME",
            "genero_cancion": "TEXT",
            "id_artista": "INT",
            "id_album": "INT"
        }
        super().__init__(db_manager, "cancion", columns, "id_cancion")