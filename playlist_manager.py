from base_manager import BaseManager

class PlaylistManager(BaseManager):
    """
    Gestiona las operaciones CRUD para la tabla 'playlist'.
    """
    def __init__(self, db_manager):
        columns = {
            "id_playlist": "SERIAL",
            "nombre_playlist": "TEXT",
            "descripcion": "TEXT",
            "id_usuario": "INT"
        }
        super().__init__(db_manager, "playlist", columns, "id_playlist")

