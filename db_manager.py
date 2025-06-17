import psycopg2
from psycopg2 import sql
import streamlit as st # Importar streamlit para mensajes

class DBManager:
    """
    Clase para gestionar la conexión a la base de datos PostgreSQL
    y la ejecución de consultas.
    """
    def __init__(self, dbname, user, password, host, port):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None # Se inicializa a None, la conexión real se hace en connect()

    @st.cache_resource # Almacena en caché la conexión para evitar reconexiones en cada rerun de Streamlit
    def get_connection(_self): # Renombrado a get_connection para ser más explícito
        """
        Establece la conexión con la base de datos y la devuelve.
        Si la conexión ya existe en caché, la reutiliza.
        """
        try:
            conn = psycopg2.connect(
                dbname=_self.dbname,
                user=_self.user,
                password=_self.password,
                host=_self.host,
                port=_self.port,
                client_encoding='UTF8' # Asegura la codificación
            )
            conn.autocommit = True # Confirmar cambios automáticamente
            st.success("Conexión a la base de datos exitosa!")
            return conn # Devolver la conexión establecida
        except psycopg2.Error as e:
            st.error(f"No se pudo conectar a la base de datos: {e}\n"
                     f"Asegúrate de que PostgreSQL esté corriendo y la base de datos '{_self.dbname}' exista. "
                     f"Verifica las credenciales: user='{_self.user}', password='{_self.password}' (¡revisa que sea la correcta!), host='{_self.host}', port='{_self.port}'.")
            return None # Devolver None si la conexión falla

    def execute_query(self, query, params=None, fetch_type=None):
        """
        Ejecuta una consulta SQL en la base de datos utilizando la conexión guardada en caché.
        :param query: La consulta SQL a ejecutar.
        :param params: Parámetros para la consulta (opcional).
        :param fetch_type: 'one' para un solo resultado, 'all' para todos, None para sin resultados.
        :return: Resultados de la consulta o None.
        """
        # Asegurarse de usar la conexión que está en caché o intentar obtenerla
        conn = self.get_connection() 
        if not conn:
            st.error("No hay una conexión activa a la base de datos.")
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if fetch_type == 'one':
                    return cursor.fetchone()
                elif fetch_type == 'all':
                    return cursor.fetchall()
                return None
        except psycopg2.Error as e:
            st.error(f"Error al ejecutar la consulta: {e}")
            return None

    def close(self):
        """
        Cierra la conexión a la base de datos si está abierta (desconecta el caché).
        """
        # st.cache_resource.clear() puede ser usado para forzar una reconexión completa
        # pero para cerrar una sesión, simplemente no se hace nada si se usa caché.
        # Si la conexión está almacenada en caché, Streamlit la gestionará.
        # Solo necesitamos el .close() en un contexto más explícito si no fuera caché.
        pass # Streamlit gestiona la conexión para @st.cache_resource

