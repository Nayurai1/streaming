from base_manager import BaseManager

class ArtistManager(BaseManager):
    """
    Gestiona las operaciones CRUD para la tabla 'artista'.
    """
    def __init__(self, db_manager):
        columns = {
            "id_artista": "SERIAL",
            "nombre_artista": "TEXT",
            "pais_artista": "TEXT",
            "anio_debut": "INT"
        }
        super().__init__(db_manager, "artista", columns, "id_artista")

