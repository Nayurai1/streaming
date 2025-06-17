from base_manager import BaseManager

class PlaylistSongManager(BaseManager):
    """
    Clase para gestionar la tabla 'playlist_cancion'.
    Hereda la funcionalidad CRUD básica de BaseManager.
    Nota: Para la clave primaria compuesta (id_playlist, id_cancion),
    la implementación genérica de BaseManager solo usará id_playlist para update/delete.
    Una implementación completa requeriría lógica específica para manejar ambas PKs.
    """
    def __init__(self, db_manager):
        columns = {
            "id_playlist": "INT",
            "id_cancion": "INT",
            "orden": "INT"
        }
        # Nota: 'id_playlist' se usa como el id_column principal para el CRUD básico.
        # Las operaciones de actualización y eliminación deberían considerar ambas claves para ser precisas.
        super().__init__(db_manager, "playlist_cancion", columns, "id_playlist")

    # Podrías anular create_record_logic, update_record_logic, delete_record_logic aquí
    # para manejar la clave primaria compuesta (id_playlist, id_cancion) de forma adecuada.
    # Por ejemplo, para delete, necesitarías ambas IDs:
    # def delete_record_logic(self, entry_widgets, tree, pagination_info, page_label):
    #     id_playlist_str = entry_widgets["id_playlist"].get()
    #     id_cancion_str = entry_widgets["id_cancion"].get()
    #     ... validación y ejecución de DELETE FROM playlist_cancion WHERE id_playlist = %s AND id_cancion = %s ...

