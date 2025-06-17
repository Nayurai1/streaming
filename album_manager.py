from base_manager import BaseManager

class AlbumManager(BaseManager):
    """
    Clase para gestionar la tabla 'album'.
    Hereda la funcionalidad CRUD básica de BaseManager.
    """
    def __init__(self, db_manager):
        columns = {
            "id_album": "INT",
            "titulo_album": "TEXT",
            "anio_album": "INT",
            "id_artista": "INT"
        }
        super().__init__(db_manager, "album", columns, "id_album")