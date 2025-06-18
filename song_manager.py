from base_manager import BaseManager

class SongManager(BaseManager):
    """
    Gestiona las operaciones CRUD para la tabla 'cancion'.
    """
    def __init__(self, db_manager):
        columns = {
            "id_cancion": "SERIAL",
            "titulo_cancion": "TEXT",
            "duracion": "TIME",
            "genero_cancion": "TEXT",
            "id_artista": "INT",
            "id_album": "INT"
        }
        super().__init__(db_manager, "cancion", columns, "id_cancion")

