import streamlit as st
import pandas as pd
from psycopg2 import sql

class ReportGenerator:
    """
    Clase para generar diversos reportes a partir de los datos de la base de datos.
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def _display_report(self, data, columns, title):
        """Función auxiliar para mostrar un DataFrame de reporte."""
        if data:
            df = pd.DataFrame(data, columns=columns)
            st.subheader(f"Resultados: {title}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No hay datos disponibles para el reporte: {title}.")

    def generate_most_played_by_country(self):
        """
        Genera un reporte de las canciones más reproducidas agrupadas por el país del usuario.
        """
        query = """
        SELECT
            u.pais AS Pais_Usuario,
            c.titulo_cancion AS Titulo_Cancion,
            a.nombre_artista AS Nombre_Artista,
            COUNT(r.id_reproduccion) AS Total_Reproducciones
        FROM
            reproduccion r
        JOIN
            usuario u ON r.id_usuario = u.id_usuario
        JOIN
            cancion c ON r.id_cancion = c.id_cancion
        JOIN
            artista a ON c.id_artista = a.id_artista
        GROUP BY
            u.pais, c.titulo_cancion, a.nombre_artista
        ORDER BY
            u.pais, Total_Reproducciones DESC;
        """
        data = self.db_manager.execute_query(sql.SQL(query), fetch_type='all')
        columns = ["Pais", "Titulo Cancion", "Artista", "Reproducciones"]
        self._display_report(data, columns, "Canciones Más Reproducidas por País de Usuario")

    def generate_artist_counts(self):
        """
        Genera un reporte que muestra el número total de álbumes y canciones
        por cada artista.
        """
        query = """
        SELECT
            ar.nombre_artista AS Artista,
            COUNT(DISTINCT al.id_album) AS Total_Albumes,
            COUNT(DISTINCT c.id_cancion) AS Total_Canciones
        FROM
            artista ar
        LEFT JOIN
            album al ON ar.id_artista = al.id_artista
        LEFT JOIN
            cancion c ON ar.id_artista = c.id_artista
        GROUP BY
            ar.nombre_artista
        ORDER BY
            Total_Albumes DESC, Total_Canciones DESC;
        """
        data = self.db_manager.execute_query(sql.SQL(query), fetch_type='all')
        columns = ["Artista", "Total Albumes", "Total Canciones"]
        self._display_report(data, columns, "Artistas con Más Álbumes y Canciones")

