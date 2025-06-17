from base_manager import BaseManager

class ReproductionManager(BaseManager):
    """
    Clase para gestionar la tabla 'reproduccion'.
    Hereda la funcionalidad CRUD básica de BaseManager.
    """
    def __init__(self, db_manager):
        columns = {
            "id_reproduccion": "INT",
            "id_usuario": "INT",
            "id_cancion": "INT",
            "fecha_reproduccion": "TIMESTAMP",
            "dispositivo": "TEXT",
            "ubicacion": "TEXT"
        }
        super().__init__(db_manager, "reproduccion", columns, "id_reproduccion")