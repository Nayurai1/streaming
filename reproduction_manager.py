from base_manager import BaseManager

class ReproductionManager(BaseManager):
    """
    Gestiona las operaciones CRUD para la tabla 'reproduccion'.
    """
    def __init__(self, db_manager):
        columns = {
            "id_reproduccion": "SERIAL",
            "id_usuario": "INT",
            "id_cancion": "INT",
            "fecha_reproduccion": "TIMESTAMP",
            "dispositivo": "TEXT",
            "ubicacion": "TEXT"
        }
        super().__init__(db_manager, "reproduccion", columns, "id_reproduccion")

