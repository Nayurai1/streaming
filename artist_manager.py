from base_manager import BaseManager

class ArtistManager(BaseManager):
    """
    Clase para gestionar la tabla 'artista'.
    Hereda la funcionalidad CRUD básica de BaseManager.
    """
    def __init__(self, db_manager):
        columns = {
            "id_artista": "INT",
            "nombre_artista": "TEXT",
            "pais_artista": "TEXT",
            "anio_debut": "INT"
        }
        super().__init__(db_manager, "artista", columns, "id_artista")