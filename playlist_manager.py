from base_manager import BaseManager

class PlaylistManager(BaseManager):
    """
    Clase para gestionar la tabla 'playlist'.
    Hereda la funcionalidad CRUD básica de BaseManager.
    """
    def __init__(self, db_manager):
        columns = {
            "id_playlist": "INT",
            "nombre_playlist": "TEXT",
            "descripcion": "TEXT",
            "id_usuario": "INT"
        }
        super().__init__(db_manager, "playlist", columns, "id_playlist")