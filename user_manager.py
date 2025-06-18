from base_manager import BaseManager

class UserManager(BaseManager):
    """
    Clase para gestionar la tabla 'usuario'.
    Hereda la funcionalidad CRUD básica de BaseManager.
    """
    def __init__(self, db_manager):
        columns = {
            "id_usuario": "SERIAL",
            "nombre": "TEXT",
            "correo": "TEXT",
            "fecha_registro": "DATE",
            "pais": "TEXT",
            "edad": "INT",
            "suscripcion_activa": "BOOLEAN"
        }
        super().__init__(db_manager, "usuario", columns, "id_usuario")

