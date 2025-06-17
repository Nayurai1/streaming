import streamlit as st # Importar streamlit para mensajes
import pandas as pd

class ReportGenerator:
    """
    Clase para generar informes basados en los datos de la base de datos.
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def generate_most_played_by_country(self):
        """
        Genera el reporte de las canciones más reproducidas por país de usuario.
        """
        query = """
            SELECT
                u.pais,
                c.titulo_cancion,
                a.nombre_artista,
                COUNT(r.id_reproduccion) AS num_reproducciones
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
                u.pais, num_reproducciones DESC;
        """
        data = self.db_manager.execute_query(query, fetch_type='all')

        if data:
            df = pd.DataFrame(data, columns=["País", "Título Canción", "Artista", "Reproducciones"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos para el reporte de canciones más reproducidas por país.")

    def generate_artist_counts(self):
        """
        Genera el reporte de artistas con más álbumes y canciones.
        """
        query = """
            SELECT
                ar.nombre_artista,
                COUNT(DISTINCT al.id_album) AS total_albumes,
                COUNT(DISTINCT ca.id_cancion) AS total_canciones
            FROM
                artista ar
            LEFT JOIN
                album al ON ar.id_artista = al.id_artista
            LEFT JOIN
                cancion ca ON ar.id_artista = ca.id_artista
            GROUP BY
                ar.nombre_artista
            ORDER BY
                total_albumes DESC, total_canciones DESC;
        """
        data = self.db_manager.execute_query(query, fetch_type='all')

        if data:
            df = pd.DataFrame(data, columns=["Artista", "Total Álbumes", "Total Canciones"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos para el reporte de artistas con más álbumes y canciones.")

