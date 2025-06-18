from base_manager import BaseManager

class AlbumManager(BaseManager):
    """
    Gestiona las operaciones CRUD para la tabla 'album'.
    """
    def __init__(self, db_manager):
        columns = {
            "id_album": "SERIAL",
            "titulo_album": "TEXT",
            "anio_album": "INT", # Nota: Tu esquema usa 'anio_album', no 'anio_lanzamiento'
            "id_artista": "INT"
        }
        super().__init__(db_manager, "album", columns, "id_album")
