import streamlit as st
import pandas as pd
import re
from datetime import datetime, date
import datetime as dt # Importar datetime como dt para evitar conflictos de nombre

# Importar tus clases de gestión
from db_manager import DBManager
from user_manager import UserManager
from artist_manager import ArtistManager
from album_manager import AlbumManager
from song_manager import SongManager
from playlist_manager import PlaylistManager
from playlist_song_manager import PlaylistSongManager
from reproduction_manager import ReproductionManager
from report_generator import ReportGenerator

# --- Función para reiniciar la sesión (cerrar sesión / cambiar usuario) ---
def _logout():
    """
    Función para limpiar el estado de la sesión y forzar un re-run al inicio de sesión.
    """
    st.session_state.db_username = ""
    st.session_state.db_password = ""
    st.cache_resource.clear() # Limpia la conexión a la BD del caché de Streamlit
    st.info("Sesión cerrada. Por favor, ingresa tus nuevas credenciales.")
    st.rerun()

# --- Configuración de la Aplicación ---
st.set_page_config(layout="wide", page_title="Plataforma de Streaming")
st.title("🎧 Plataforma de Streaming - Gestión de Datos")

# --- Botón de Cerrar Sesión / Cambiar Usuario (arriba a la izquierda en sidebar) ---
st.sidebar.button("🔴 Cerrar Sesión / Cambiar Usuario", type="secondary", on_click=_logout)


# --- Sección de Inicio de Sesión (Login) ---
st.sidebar.header("🔑 Inicio de Sesión de Base de Datos")

# Inicializar credenciales en session_state si no existen
if 'db_username' not in st.session_state:
    st.session_state.db_username = "postgres" # Valor por defecto
if 'db_password' not in st.session_state:
    st.session_state.db_password = "123456"   # Valor por defecto

# Entradas para usuario y contraseña
username_input = st.sidebar.text_input("Usuario de BD:", value=st.session_state.db_username, key="login_username_input")
password_input = st.sidebar.text_input("Contraseña de BD:", type="password", value=st.session_state.db_password, key="login_password_input")

# Botón para conectar
if st.sidebar.button("Conectar a Base de Datos", key="connect_db_button"):
    # Limpiar caché de Streamlit para forzar una nueva conexión
    st.cache_resource.clear()

    # Actualizar credenciales en session_state
    st.session_state.db_username = username_input
    st.session_state.db_password = password_input
    
    st.success("Intentando conectar...")
    st.rerun() # Forzar un rerun para que el nuevo DBManager se cree y conecte

# --- Intentar obtener la conexión al inicio de cada rerun ---
# Solo instanciamos DBManager si tenemos credenciales
db_manager = None # Inicializar db_manager a None
if st.session_state.db_username and st.session_state.db_password:
    db_manager = DBManager(
        dbname="plataforma_streaming",
        user=st.session_state.db_username,
        password=st.session_state.db_password,
        host="localhost",
        port="5432"
    )
    # Intentamos obtener la conexión real de psycopg2 a través del manager
    conn_status = db_manager.get_connection() 
    if conn_status is None:
        # Si get_connection devolvió None, significa que la conexión falló
        st.error("No se pudo establecer la conexión a la base de datos. Por favor, revisa tus credenciales y el estado del servidor PostgreSQL.")
        st.stop() # Detiene la ejecución si la conexión no es válida
else:
    st.info("Por favor, ingresa tus credenciales de PostgreSQL y haz clic en 'Conectar a Base de Datos' en el menú lateral.")
    st.stop() # Detiene la ejecución si no hay credenciales

# Si llegamos aquí, significa que db_manager.get_connection() tuvo éxito.
st.sidebar.success("Conectado a la BD como: " + st.session_state.db_username)


# --- Inicialización de Session State para la UI (solo si la BD está conectada) ---
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Usuarios"

if 'crud_form_data' not in st.session_state:
    st.session_state.crud_form_data = {}
if 'pagination_info' not in st.session_state:
    st.session_state.pagination_info = {}
if 'filter_settings' not in st.session_state:
    st.session_state.filter_settings = {}
if 'editing_record_id' not in st.session_state:
    st.session_state.editing_record_id = None
if 'loaded_record_data' not in st.session_state:
    st.session_state.loaded_record_data = {}


# --- Instanciar Managers (se hacen una vez que db_manager es válido) ---
user_manager = UserManager(db_manager)
artist_manager = ArtistManager(db_manager)
album_manager = AlbumManager(db_manager)
song_manager = SongManager(db_manager)
playlist_manager = PlaylistManager(db_manager)
playlist_song_manager = PlaylistSongManager(db_manager)
reproduction_manager = ReproductionManager(db_manager)
report_generator = ReportGenerator(db_manager)

# Mapear los managers a las pestañas para poder acceder a foreign_key_columns
manager_map = {
    "Usuarios": user_manager,
    "Artistas": artist_manager,
    "Álbumes": album_manager,
    "Canciones": song_manager,
    "Playlists": playlist_manager,
    "Playlist-Canción": playlist_song_manager,
    "Reproducciones": reproduction_manager
}


# --- Función Auxiliar para Renderizar Campos de Entrada (para evitar repetición) ---
def _render_input_field(col_name, col_type, column_container, initial_value, key):
    """
    Renderiza un campo de entrada de Streamlit basado en el tipo de columna.
    """
    if col_type == "INT":
        try:
            # Asegura que el valor inicial sea None o un entero para number_input
            init_val = int(initial_value) if str(initial_value).replace('.','',1).isdigit() else None
        except ValueError:
            init_val = None
        return column_container.number_input(
            f"{col_name.replace('_', ' ').title()}:", value=init_val, format="%d", key=key
        )
    elif col_type == "BOOLEAN":
        # Convierte el string "true"/"false" a booleano
        init_val = True if str(initial_value).lower() == 'true' else (False if str(initial_value).lower() == 'false' else False)
        return column_container.checkbox(f"{col_name.replace('_', ' ').title()}:", value=init_val, key=key)
    elif col_type == "DATE":
        try:
            # Convierte el string de fecha a objeto date
            init_val = datetime.strptime(str(initial_value), "%Y-%m-%d").date() if initial_value else None
        except ValueError:
            init_val = None # Si el formato no coincide, no pre-rellenar
        return column_container.date_input(f"{col_name.replace('_', ' ').title()}:", value=init_val, key=key)
    elif col_type == "TIME":
        # Streamlit no tiene un widget de hora directo, usar text_input
        return column_container.text_input(f"{col_name.replace('_', ' ').title()} (HH:MM:SS):", value=str(initial_value)[:8] if initial_value else "", key=key)
    elif col_type == "TIMESTAMP":
        # Streamlit no tiene un widget de timestamp directo, usar text_input
        return column_container.text_input(f"{col_name.replace('_', ' ').title()} (YYYY-MM-DD HH:MM:SS):", value=str(initial_value) if initial_value else "", key=key)
    else: # TEXT
        return column_container.text_input(f"{col_name.replace('_', ' ').title()}:", value=str(initial_value) if initial_value else "", key=key)


# --- Función Principal para Renderizar el CRUD (con Expanders) ---
def render_crud_tab(manager, key_prefix):
    """
    Renderiza la interfaz CRUD para una tabla específica usando expanders.
    """
    st.header(f"Gestión de {manager.table_name.capitalize()}")

    # Inicializar st.session_state para esta tabla específica si no existe
    if manager.table_name not in st.session_state.crud_form_data:
        st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns}
    if manager.table_name not in st.session_state.pagination_info:
        st.session_state.pagination_info[manager.table_name] = {"offset": 0, "limit": 10, "current_page": 1, "total_records": 0}
    if manager.table_name not in st.session_state.filter_settings:
        st.session_state.filter_settings[manager.table_name] = {"column": "", "value": ""}

    # current_form_data almacena los valores que se cargan o se están editando
    current_form_data = st.session_state.crud_form_data[manager.table_name]
    current_pagination_info = st.session_state.pagination_info[manager.table_name]
    current_filter_settings = st.session_state.filter_settings[manager.table_name]

    # --- Sección "Crear Nuevo Registro" ---
    with st.expander("➕ Crear Nuevo Registro"):
        st.subheader("Ingresa los datos para crear un nuevo registro:")
        
        with st.form(key=f"{key_prefix}_create_form"):
            create_form_values = {}
            create_cols = st.columns(3)
            col_idx = 0
            for col_name, col_type in manager.columns.items():
                if col_name == manager.id_column: # NO mostrar ID para la creación (es automático)
                    continue
                create_form_values[col_name] = _render_input_field(
                    col_name, col_type, create_cols[col_idx % 3], 
                    "", # Vacío para la creación
                    f"{key_prefix}_create_{col_name}_input"
                )
                col_idx += 1
            
            submitted_create = st.form_submit_button("Crear Registro")
            if submitted_create:
                # Actualizar session_state con los valores del formulario al hacer submit
                for col_name, value in create_form_values.items():
                    st.session_state.crud_form_data[manager.table_name][col_name] = value
                
                # Ejecutar la lógica de creación
                if manager.create_record_logic(st.session_state.crud_form_data[manager.table_name]):
                    st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns} # Limpiar formulario
                    st.rerun() # Rerender para mostrar datos actualizados

    # --- Sección "Actualizar Registro Existente" ---
    # Eliminar "🔍 Leer / Cargar Registro Existente" como sección separada
    # La funcionalidad de carga se integra aquí para el UX.
    with st.expander("✏️ Actualizar Registro Existente"):
        st.subheader("1. Carga un registro para precargar sus datos (opcional):")
        
        with st.form(key=f"{key_prefix}_load_for_update_form"):
            load_id_input = st.text_input(f"{manager.id_column.replace('_', ' ').title()} (ID del Registro a Cargar):", 
                                           value=current_form_data.get(manager.id_column, ""), 
                                           key=f"{key_prefix}_load_id_input_form")
            
            submitted_load = st.form_submit_button("Cargar Datos del Registro")
            if submitted_load:
                loaded_data = manager.load_selected_record_logic(load_id_input)
                if loaded_data:
                    st.session_state.crud_form_data[manager.table_name] = loaded_data
                    st.rerun() # Recargar para que los campos de abajo se precarguen

        st.subheader("2. Modifica los campos y actualiza:")
        st.info("Ingresa el ID del registro que deseas actualizar. Todos los demás campos de la tabla son editables.")
        
        with st.form(key=f"{key_prefix}_update_form"):
            update_form_values = {}
            update_cols = st.columns(3)
            col_idx = 0

            # Campo específico para el ID de la tabla actual (clave primaria)
            id_update_input = update_cols[col_idx % 3].text_input(
                f"**{manager.id_column.replace('_', ' ').title()} (ID del Registro a Actualizar):**", # Hacer más prominente
                value=str(current_form_data.get(manager.id_column, "")),
                key=f"{key_prefix}_update_{manager.id_column}_main_input" # Clave única y clara
            )
            update_form_values[manager.id_column] = id_update_input # Guardar el ID en el diccionario
            col_idx += 1

            # Renderizar el resto de los campos, INCLUYENDO las claves foráneas
            # Ya no se excluyen las claves foráneas aquí
            for col_name, col_type in manager.columns.items():
                if col_name == manager.id_column: # Ya lo renderizamos arriba
                    continue
                
                # Renderizar TODOS los campos de datos restantes (incluidas las claves foráneas)
                # El base_manager.py ya maneja si un campo se deja vacío (lo pone a NULL si es posible)
                update_form_values[col_name] = _render_input_field(
                    col_name, col_type, update_cols[col_idx % 3], 
                    current_form_data.get(col_name, ""), # Usar el valor cargado/actual
                    f"{key_prefix}_update_{col_name}_data_input" # Clave única y clara
                )
                col_idx += 1
            
            submitted_update = st.form_submit_button("Actualizar Registro")
            if submitted_update:
                # Actualizar session_state con los valores del formulario
                # Solo los campos renderizados estarán en update_form_values
                st.session_state.crud_form_data[manager.table_name].update(update_form_values) 

                # Asegurarse de que el ID primario se use del campo específico
                st.session_state.crud_form_data[manager.table_name][manager.id_column] = id_update_input

                # Ejecutar la lógica de actualización
                if manager.update_record_logic(st.session_state.crud_form_data[manager.table_name]):
                    st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns} # Limpiar formulario
                    st.rerun()

    # --- Sección "Eliminar Registro" ---
    with st.expander("🗑️ Eliminar Registro"):
        st.subheader("Ingresa el ID del registro que deseas eliminar permanentemente:")
        
        with st.form(key=f"{key_prefix}_delete_form"):
            delete_id_input = st.text_input(f"{manager.id_column.replace('_', ' ').title()} (ID):", 
                                            value=current_form_data.get(manager.id_column, ""), 
                                            key=f"{key_prefix}_delete_id_input_form") # Clave única
            
            submitted_delete = st.form_submit_button("Eliminar Registro")
            if submitted_delete:
                if manager.delete_record_logic(delete_id_input):
                    st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns} # Limpiar formulario
                    st.rerun()

    # --- Sección de Filtro y Paginación (siempre visible) ---
    st.subheader("Datos de la Tabla")
    
    filter_cols = st.columns([0.2, 0.4, 0.2, 0.2])
    filter_column_options = [""] + [col for col in manager.columns.keys() if col != manager.id_column] # Permite no seleccionar filtro
    
    selected_filter_column = filter_cols[0].selectbox(
        "Columna a Filtrar:",
        options=filter_column_options,
        key=f"{key_prefix}_filter_col",
        index=filter_column_options.index(current_filter_settings["column"]) if current_filter_settings["column"] in filter_column_options else 0
    )
    filter_value = filter_cols[1].text_input(
        "Valor de Filtro:",
        value=current_filter_settings["value"],
        key=f"{key_prefix}_filter_val"
    )

    # Actualizar settings de filtro en session_state
    st.session_state.filter_settings[manager.table_name]["column"] = selected_filter_column
    st.session_state.filter_settings[manager.table_name]["value"] = filter_value

    if filter_cols[2].button("Aplicar Filtro", key=f"{key_prefix}_apply_filter_btn"):
        current_pagination_info["offset"] = 0 # Reiniciar paginación al filtrar
        current_pagination_info["current_page"] = 1
        st.rerun() # Rerender para aplicar el filtro

    if filter_cols[3].button("Limpiar Filtro", key=f"{key_prefix}_clear_filter_btn"):
        st.session_state.filter_settings[manager.table_name]["column"] = ""
        st.session_state.filter_settings[manager.table_name]["value"] = ""
        current_pagination_info["offset"] = 0 # Reiniciar paginación al limpiar
        current_pagination_info["current_page"] = 1
        st.rerun() # Rerender para limpiar el filtro

    # Placeholders para la tabla y la paginación (se llenarán en load_data_logic)
    table_placeholder = st.empty()
    pagination_label_placeholder = st.empty()
    pagination_buttons_cols = st.columns([0.1, 0.1])

    # Lógica de carga de datos (usando el filtro y paginación actuales)
    manager.load_data_logic(
        table_placeholder,
        current_pagination_info,
        pagination_label_placeholder,
        page_change=0, # No cambiar de página de inmediato
        filter_column=current_filter_settings["column"],
        filter_value=current_filter_settings["value"]
    )

    # Botones de Paginación
    if pagination_buttons_cols[0].button("Anterior", key=f"{key_prefix}_prev_page_btn"):
        manager.load_data_logic(
            table_placeholder,
            current_pagination_info,
            pagination_label_placeholder,
            page_change=-1,
            filter_column=current_filter_settings["column"],
            filter_value=current_filter_settings["value"]
        )
    if pagination_buttons_cols[1].button("Siguiente", key=f"{key_prefix}_next_page_btn"):
        manager.load_data_logic(
            table_placeholder,
            current_pagination_info,
            pagination_label_placeholder,
            page_change=1,
            filter_column=current_filter_settings["column"],
            filter_value=current_filter_settings["value"]
        )

# --- Renderizar Pestañas de Reportes ---
def render_reports_tab():
    st.header("📊 Reportes de Negocio")

    st.subheader("Canciones Más Reproducidas por País de Usuario")
    st.write("Este reporte muestra las canciones más populares agrupadas por el país del usuario que las reproduce.")
    if st.button("Generar Reporte de Canciones por País", key="report_songs_by_country"):
        report_generator.generate_most_played_by_country()
        
    st.markdown("---") # Separador visual

    st.subheader("Artistas con Más Álbumes y Canciones")
    st.write("Este reporte lista los artistas y el total de álbumes y canciones asociadas a ellos.")
    if st.button("Generar Reporte de Artistas y Contenido", key="report_artist_content"):
        report_generator.generate_artist_counts()


# --- Renderizar Pestaña de Consultas SQL Directas ---
def render_direct_query_tab():
    st.header("🔧 Consultas SQL Directas")
    # Se elimina la validación restrictiva de SELECT al inicio
    st.warning("¡ADVERTENCIA DE SEGURIDAD! El uso incorrecto de consultas SQL puede causar errores. Solo se esperará que sean consultas SELECT.")

    query_string = st.text_area("Introduce tu consulta SQL aquí:", height=200, key="direct_sql_query_input")

    if st.button("Ejecutar Consulta", key="execute_direct_query_btn"):
        if not query_string:
            st.error("La consulta no puede estar vacía.")
            return

        # Validación más flexible: Permitimos cualquier SELECT válido
        # Se elimina la validación estricta de `re.match(r"^\s*SELECT\s+"...`
        try:
            # Asegurarse de que db_manager.connection es la conexión real de psycopg2
            conn = db_manager.get_connection()
            if not conn: # Doble verificación si la conexión es None
                st.error("No hay una conexión activa a la base de datos para ejecutar la consulta.")
                return

            with conn.cursor() as cursor:
                cursor.execute(query_string)
                results = cursor.fetchall()
                
                if cursor.description: # Si la consulta devuelve filas (ej. es un SELECT)
                    column_names = [desc[0] for desc in cursor.description]
                    df_results = pd.DataFrame(results, columns=column_names)
                    st.subheader("Resultados de la Consulta")
                    st.dataframe(df_results, use_container_width=True, hide_index=True)
                else: # Si la consulta no devuelve filas (ej. un SELECT sin resultados, o DDL/DML que no debería pasar aquí)
                    st.info("Consulta ejecutada. No se esperaban resultados (ej. DDL/DML que no devuelve filas).")

        except Exception as e:
            st.error(f"Error al ejecutar la consulta:\n{e}")

# --- Navegación Principal (Sidebar) ---
st.sidebar.title("Menú de Navegación")
tabs = {
    "Usuarios": lambda: render_crud_tab(user_manager, "user"),
    "Artistas": lambda: render_crud_tab(artist_manager, "artist"),
    "Álbumes": lambda: render_crud_tab(album_manager, "album"),
    "Canciones": lambda: render_crud_tab(song_manager, "song"),
    "Playlists": lambda: render_crud_tab(playlist_manager, "playlist"),
    "Playlist-Canción": lambda: render_crud_tab(playlist_song_manager, "playlist_song"),
    "Reproducciones": lambda: render_crud_tab(reproduction_manager, "reproduction"),
    "Reportes": render_reports_tab,
    "Consultas SQL Directas": render_direct_query_tab
}

selected_tab = st.sidebar.radio("Selecciona una pestaña:", list(tabs.keys()), key="sidebar_tab_selector")

# Renderizar la pestaña seleccionada
tabs[selected_tab]()
