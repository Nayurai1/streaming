import psycopg2
import streamlit as st
from psycopg2 import sql

@st.cache_resource(ttl=3600) # La conexión se mantendrá en caché por 1 hora
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
        self.connection = None

    def connect(self):
        """
        Establece la conexión con la base de datos.
        """
        try:
            self.connection = psycopg2.connect(
                dbname=self.dbname, # Usará "streaming_db" pasado desde app.py
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                client_encoding='UTF8' # Asegura la codificación UTF-8
            )
            self.connection.autocommit = True
            return True # Indicar que la conexión fue exitosa
        except psycopg2.Error as e:
            st.error(f"No se pudo conectar a la base de datos: {e}\n"
                     f"Asegúrate de que PostgreSQL esté corriendo y la base de datos '{self.dbname}' exista.")
            return False # Indicar que la conexión falló

    def execute_query(self, query, params=None, fetch_type=None):
        """
        Ejecuta una consulta SQL en la base de datos.
        :param query: La consulta SQL a ejecutar.
        :param params: Parámetros para la consulta (opcional).
        :param fetch_type: 'one' para un solo resultado, 'all' para todos, None para sin resultados.
        :return: Resultados de la consulta o None.
        """
        if not self.connection:
            st.error("No hay conexión a la base de datos. Por favor, conecta primero.")
            return None
        try:
            with self.connection.cursor() as cursor:
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
        Cierra la conexión a la base de datos si está abierta.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            st.info("Conexión a la base de datos cerrada.")

