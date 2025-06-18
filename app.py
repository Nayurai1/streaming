import streamlit as st
import pandas as pd
from datetime import datetime, date, time # Importar time explícitamente

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

# --- Configuración de la Aplicación ---
st.set_page_config(layout="wide", page_title="Plataforma de Streaming")
st.title("🎧 Plataforma de Streaming - Gestión de Datos")

# --- Inicialización de Session State (siempre al inicio) ---
if 'db_username' not in st.session_state:
    st.session_state.db_username = "postgres"
if 'db_password' not in st.session_state:
    st.session_state.db_password = "admin"
if 'db_connected' not in st.session_state:
    st.session_state.db_connected = False
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Usuarios"
if 'crud_form_data' not in st.session_state:
    st.session_state.crud_form_data = {}
if 'pagination_info' not in st.session_state:
    st.session_state.pagination_info = {}
if 'filter_settings' not in st.session_state:
    st.session_state.filter_settings = {}
if 'last_op_type' not in st.session_state:
    st.session_state.last_op_type = {} # Para rastrear el último tipo de operación por tabla
if 'show_crud_fields' not in st.session_state:
    st.session_state.show_crud_fields = {} # Controla la visibilidad de los campos por tabla/operación


# --- Función para reiniciar sesión ---
def logout():
    st.session_state.db_connected = False
    st.session_state.db_username = "postgres" # O limpiar a "" si quieres que se reingrese siempre
    st.session_state.db_password = "admin" # O limpiar a ""
    st.cache_resource.clear() # Limpiar la caché de recursos para forzar nueva conexión
    st.rerun() # Forzar un re-render para volver a la página de login

# --- Interfaz de Inicio de Sesión Grande ---
def login_page():
    # Limpiar contenido anterior si existe
    st.empty()

    # Centrar el contenido de la pantalla de login
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2: # Usar la columna central para el formulario de login
        st.markdown("<h2 style='text-align: center;'>🔑 Iniciar Sesión para Conectar a la Base de Datos</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Por favor, ingresa tus credenciales de PostgreSQL (base de datos: <strong>streaming_db</strong>).</p>", unsafe_allow_html=True)

        # Entradas para usuario y contraseña
        username_input = st.text_input(
            "Usuario de BD:",
            value=st.session_state.db_username,
            key="login_page_username_input"
        )
        password_input = st.text_input(
            "Contraseña de BD:",
            type="password",
            value=st.session_state.db_password,
            key="login_page_password_input"
        )

        # Botón para conectar
        if st.button("Conectar a Base de Datos", key="login_page_connect_db_button", use_container_width=True):
            # Limpiar caché de Streamlit para forzar una nueva conexión
            st.cache_resource.clear()

            # Actualizar credenciales en session_state
            st.session_state.db_username = username_input
            st.session_state.db_password = password_input

            # Intentar conectar
            db_manager_attempt = DBManager(
                dbname="streaming_db", # Base de datos definida
                user=st.session_state.db_username,
                password=st.session_state.db_password,
                host="localhost",
                port="5432"
            )
            if db_manager_attempt.connect():
                st.session_state.db_connected = True
                st.success("Conectado exitosamente. Cargando aplicación...")
                st.rerun() # Forzar un re-render para mostrar la app principal
            else:
                st.session_state.db_connected = False
                st.error("Falló la conexión a la base de datos con las credenciales proporcionadas.")

# --- Función Auxiliar para Renderizar Formulario CRUD y Tabla ---
def render_crud_tab(manager, key_prefix):
    """
    Renderiza la interfaz CRUD para una tabla específica con selectbox de operaciones.
    """
    st.header(f"Gestión de {manager.table_name.capitalize()}")

    # Inicializar session_state para esta tabla específica si no existe
    if manager.table_name not in st.session_state.crud_form_data:
        st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns}
    if manager.table_name not in st.session_state.pagination_info:
        st.session_state.pagination_info[manager.table_name] = {"offset": 0, "limit": 10, "current_page": 1, "total_records": 0}
    if manager.table_name not in st.session_state.filter_settings:
        st.session_state.filter_settings[manager.table_name] = {"column": "", "value": ""}
    if manager.table_name not in st.session_state.last_op_type:
        st.session_state.last_op_type[manager.table_name] = None # Para rastrear el último tipo de operación por tabla
    if manager.table_name not in st.session_state.show_crud_fields:
        st.session_state.show_crud_fields[manager.table_name] = False # Por defecto no mostrar campos


    current_form_data = st.session_state.crud_form_data[manager.table_name]
    current_pagination_info = st.session_state.pagination_info[manager.table_name]
    current_filter_settings = st.session_state.filter_settings[manager.table_name]

    # --- Selección de Operación CRUD ---
    st.subheader("Selecciona una Operación")
    selected_crud_op = st.selectbox(
        "Operación:",
        ["", "➕ Crear", "✏️ Actualizar", "🗑️ Eliminar"], # Añadir una opción vacía inicial
        key=f"{key_prefix}_crud_op_selector"
    )

    # Detectar cambio de operación para limpiar/resetear formulario y controlar visibilidad
    if selected_crud_op != st.session_state.last_op_type[manager.table_name]:
        st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns} # Limpiar todo al cambiar de operación
        st.session_state.last_op_type[manager.table_name] = selected_crud_op
        
        # Ocultar campos por defecto al cambiar de operación o si la operación es vacía
        st.session_state.show_crud_fields[manager.table_name] = False 
        
        # Si se selecciona Crear, mostrar los campos inmediatamente
        if selected_crud_op == "➕ Crear":
            st.session_state.show_crud_fields[manager.table_name] = True
        
        # Re-run para aplicar los cambios de visibilidad y limpiar el formulario
        st.rerun() 
    
    # --- Campos de Entrada del Formulario (Condicionales) ---
    st.subheader("Datos del Registro")

    # Si la operación es "Crear", mostrar todos los campos excepto el ID (que es SERIAL)
    if selected_crud_op == "➕ Crear":
        cols_for_other_fields = st.columns(3) # Para organizar entradas en columnas
        col_idx = 0
        for col_name, col_type in manager.columns.items():
            if col_name == manager.id_column: # El ID es SERIAL, no se inserta manualmente
                continue

            current_value = st.session_state.crud_form_data[manager.table_name].get(col_name, "")
            
            # Renderizar campo según tipo
            if col_type == "INT":
                try:
                    init_val = int(current_value) if str(current_value).isdigit() else None
                    input_value = cols_for_other_fields[col_idx % 3].number_input(
                        f"{col_name.replace('_', ' ').title()}:",
                        value=init_val, format="%d", key=f"{key_prefix}_{col_name}_input_create"
                    )
                except ValueError:
                    input_value = cols_for_other_fields[col_idx % 3].number_input(
                        f"{col_name.replace('_', ' ').title()}:",
                        value=None, format="%d", key=f"{key_prefix}_{col_name}_input_create"
                    )
            elif col_type == "BOOLEAN":
                init_val = True if str(current_value).lower() == 'true' else (False if str(current_value).lower() == 'false' else False)
                input_value = cols_for_other_fields[col_idx % 3].checkbox(
                    f"{col_name.replace('_', ' ').title()}:",
                    value=init_val, key=f"{key_prefix}_{col_name}_input_create"
                )
            elif col_type == "DATE":
                try:
                    init_val = datetime.strptime(str(current_value), "%Y-%m-%d").date() if current_value else None
                except ValueError:
                    init_val = None
                input_value = cols_for_other_fields[col_idx % 3].date_input(
                    f"{col_name.replace('_', ' ').title()}:",
                    value=init_val, key=f"{key_prefix}_{col_name}_input_create"
                )
            elif col_type == "TIME":
                input_value = cols_for_other_fields[col_idx % 3].text_input(
                    f"{col_name.replace('_', ' ').title()} (HH:MM:SS):",
                    value=str(current_value)[:8] if current_value else "", key=f"{key_prefix}_{col_name}_input_create"
                )
            elif col_type == "TIMESTAMP":
                input_value = cols_for_other_fields[col_idx % 3].text_input(
                    f"{col_name.replace('_', ' ').title()} (YYYY-MM-DD HH:MM:SS):",
                    value=str(current_value) if current_value else "", key=f"{key_prefix}_{col_name}_input_create"
                )
            else: # TEXT
                input_value = cols_for_other_fields[col_idx % 3].text_input(
                    f"{col_name.replace('_', ' ').title()}:",
                    value=str(current_value) if current_value else "", key=f"{key_prefix}_{col_name}_input_create"
                )
            st.session_state.crud_form_data[manager.table_name][col_name] = input_value
            col_idx += 1
        
        # Botón de crear
        if st.button("➕ Crear Registro", key=f"{key_prefix}_create_btn", use_container_width=True):
            if manager.create_record_logic(st.session_state.crud_form_data[manager.table_name]):
                st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns}
                st.session_state.show_crud_fields[manager.table_name] = False # Ocultar campos después de crear
                st.session_state.last_op_type[manager.table_name] = "" # Resetear selectbox
                st.rerun()

    # Si la operación es "Actualizar", primero pedir ID, luego mostrar todos los campos
    elif selected_crud_op == "✏️ Actualizar":
        id_placeholder_value = str(current_form_data.get(manager.id_column, "")) if current_form_data.get(manager.id_column) else ""
        id_input_value = st.text_input(
            f"{manager.id_column.replace('_', ' ').title()} (ID del registro a actualizar):",
            value=id_placeholder_value,
            key=f"{key_prefix}_{manager.id_column}_input_update_id_only"
        )
        st.session_state.crud_form_data[manager.table_name][manager.id_column] = id_input_value # Actualizar Session State

        # Botón para cargar el registro
        if st.button("⬇️ Cargar datos para actualizar", key=f"{key_prefix}_load_for_update_btn", use_container_width=True):
            record_id_to_load = st.session_state.crud_form_data[manager.table_name].get(manager.id_column)
            loaded_data = manager.load_selected_record_logic(record_id_to_load)
            if loaded_data:
                st.session_state.crud_form_data[manager.table_name] = loaded_data
                st.session_state.show_crud_fields[manager.table_name] = True # Mostrar campos después de cargar
                st.rerun() # Forzar re-render para mostrar datos cargados y habilitar inputs
            else:
                st.session_state.show_crud_fields[manager.table_name] = False # Ocultar si no se pudo cargar

        if st.session_state.show_crud_fields[manager.table_name]:
            st.markdown("---") # Separador visual
            st.subheader("Modificar Datos")
            cols_for_other_fields = st.columns(3) # Para organizar entradas en columnas
            col_idx = 0
            for col_name, col_type in manager.columns.items():
                if col_name == manager.id_column:
                    continue # ID ya manejado y no se debe modificar

                current_value = st.session_state.crud_form_data[manager.table_name].get(col_name, "")
                
                # Renderizar campo según tipo
                if col_type == "INT":
                    try:
                        init_val = int(current_value) if str(current_value).isdigit() else None
                        input_value = cols_for_other_fields[col_idx % 3].number_input(
                            f"{col_name.replace('_', ' ').title()}:",
                            value=init_val, format="%d", key=f"{key_prefix}_{col_name}_input_update"
                        )
                    except ValueError:
                        input_value = cols_for_other_fields[col_idx % 3].number_input(
                            f"{col_name.replace('_', ' ').title()}:",
                            value=None, format="%d", key=f"{key_prefix}_{col_name}_input_update"
                        )
                elif col_type == "BOOLEAN":
                    init_val = True if str(current_value).lower() == 'true' else (False if str(current_value).lower() == 'false' else False)
                    input_value = cols_for_other_fields[col_idx % 3].checkbox(
                        f"{col_name.replace('_', ' ').title()}:",
                        value=init_val, key=f"{key_prefix}_{col_name}_input_update"
                    )
                elif col_type == "DATE":
                    try:
                        init_val = datetime.strptime(str(current_value), "%Y-%m-%d").date() if current_value else None
                    except ValueError:
                        init_val = None
                    input_value = cols_for_other_fields[col_idx % 3].date_input(
                        f"{col_name.replace('_', ' ').title()}:",
                        value=init_val, key=f"{key_prefix}_{col_name}_input_update"
                    )
                elif col_type == "TIME":
                    input_value = cols_for_other_fields[col_idx % 3].text_input(
                        f"{col_name.replace('_', ' ').title()} (HH:MM:SS):",
                        value=str(current_value)[:8] if current_value else "", key=f"{key_prefix}_{col_name}_input_update"
                    )
                elif col_type == "TIMESTAMP":
                    input_value = cols_for_other_fields[col_idx % 3].text_input(
                        f"{col_name.replace('_', ' ').title()} (YYYY-MM-DD HH:MM:SS):",
                        value=str(current_value) if current_value else "", key=f"{key_prefix}_{col_name}_input_update"
                    )
                else: # TEXT
                    input_value = cols_for_other_fields[col_idx % 3].text_input(
                        f"{col_name.replace('_', ' ').title()}:",
                        value=str(current_value) if current_value else "", key=f"{key_prefix}_{col_name}_input_update"
                    )
                st.session_state.crud_form_data[manager.table_name][col_name] = input_value
                col_idx += 1
            
            if st.button("💾 Guardar Cambios (Actualizar)", key=f"{key_prefix}_update_btn", use_container_width=True):
                if manager.update_record_logic(st.session_state.crud_form_data[manager.table_name]):
                    st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns}
                    st.session_state.show_crud_fields[manager.table_name] = False # Ocultar campos después de actualizar
                    st.session_state.last_op_type[manager.table_name] = "" # Resetear selectbox
                    st.rerun()

    # Si la operación es "Eliminar", solo pedir ID
    elif selected_crud_op == "🗑️ Eliminar":
        id_placeholder_value = str(current_form_data.get(manager.id_column, "")) if current_form_data.get(manager.id_column) else ""
        id_input_value = st.text_input(
            f"{manager.id_column.replace('_', ' ').title()} (ID del registro a eliminar):",
            value=id_placeholder_value,
            key=f"{key_prefix}_{manager.id_column}_input_delete_only"
        )
        st.session_state.crud_form_data[manager.table_name][manager.id_column] = id_input_value # Actualizar Session State
        
        if st.button("🗑️ Eliminar Registro", key=f"{key_prefix}_delete_btn", use_container_width=True):
            record_id_to_delete = st.session_state.crud_form_data[manager.table_name].get(manager.id_column)
            if manager.delete_record_logic(record_id_to_delete):
                st.session_state.crud_form_data[manager.table_name] = {col: "" for col in manager.columns}
                st.session_state.show_crud_fields[manager.table_name] = False # Ocultar campos después de eliminar
                st.session_state.last_op_type[manager.table_name] = "" # Resetear selectbox
                st.rerun()

    # --- Sección de Filtro y Paginación ---
    st.subheader("Datos de la Tabla")

    filter_cols = st.columns([0.2, 0.4, 0.2, 0.2])
    filter_column_options = [""] + [col for col in manager.columns.keys() if col != manager.id_column]

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

    if filter_cols[2].button("🔍 Aplicar Filtro", key=f"{key_prefix}_apply_filter_btn"):
        current_pagination_info["offset"] = 0 # Reiniciar paginación al filtrar
        current_pagination_info["current_page"] = 1
        st.rerun() # Rerender para aplicar el filtro

    if filter_cols[3].button("🧹 Limpiar Filtro", key=f"{key_prefix}_clear_filter_btn"):
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
    if pagination_buttons_cols[0].button("⬅️ Anterior", key=f"{key_prefix}_prev_page_btn"):
        manager.load_data_logic(
            table_placeholder,
            current_pagination_info,
            pagination_label_placeholder,
            page_change=-1,
            filter_column=current_filter_settings["column"],
            filter_value=current_filter_settings["value"]
        )
    if pagination_buttons_cols[1].button("Siguiente ➡️", key=f"{key_prefix}_next_page_btn"):
        manager.load_data_logic(
            table_placeholder,
            current_pagination_info,
            pagination_label_placeholder,
            page_change=1,
            filter_column=current_filter_settings["column"],
            filter_value=current_filter_settings["value"]
        )

# --- Lógica Principal de la Aplicación ---
if not st.session_state.db_connected:
    login_page() # Mostrar solo la página de login si no hay conexión
else:
    # --- Una vez conectado, inicializar DBManager y los Managers ---
    # @st.cache_resource asegura que esto se ejecute una sola vez por sesión
    @st.cache_resource(ttl=3600)
    def get_db_and_managers(username, password):
        db_manager = DBManager(
            dbname="streaming_db",
            user=username,
            password=password,
            host="localhost",
            port="5432"
        )
        # Intentar conectar de nuevo, por si se borró la caché o cambió el contexto
        if not db_manager.connection:
            if not db_manager.connect():
                st.error("Re-conexión a la base de datos fallida. Por favor, intenta de nuevo.")
                st.session_state.db_connected = False
                st.rerun() # Volver a la página de login

        # Inicializar todos los managers con la instancia de db_manager
        user_manager = UserManager(db_manager)
        artist_manager = ArtistManager(db_manager)
        album_manager = AlbumManager(db_manager)
        song_manager = SongManager(db_manager)
        playlist_manager = PlaylistManager(db_manager)
        playlist_song_manager = PlaylistSongManager(db_manager)
        reproduction_manager = ReproductionManager(db_manager)
        report_generator = ReportGenerator(db_manager) # Se mantiene la instancia por si se quiere usar internamente

        return {
            "db_manager": db_manager,
            "user_manager": user_manager,
            "artist_manager": artist_manager,
            "album_manager": album_manager,
            "song_manager": song_manager,
            "playlist_manager": playlist_manager,
            "playlist_song_manager": playlist_song_manager,
            "reproduction_manager": reproduction_manager,
            "report_generator": report_generator
        }

    # Obtener las instancias de los managers (se cargarán de caché si ya están)
    managers = get_db_and_managers(st.session_state.db_username, st.session_state.db_password)

    # --- Navegación Principal (Sidebar) ---
    st.sidebar.title("Menú de Navegación")
    tabs = {
        "👥 Usuarios": lambda: render_crud_tab(managers["user_manager"], "user"),
        "🎤 Artistas": lambda: render_crud_tab(managers["artist_manager"], "artist"),
        "💿 Álbumes": lambda: render_crud_tab(managers["album_manager"], "album"),
        "🎶 Canciones": lambda: render_crud_tab(managers["song_manager"], "song"),
        "📝 Playlists": lambda: render_crud_tab(managers["playlist_manager"], "playlist"),
        "🔗 Playlist-Canción": lambda: render_crud_tab(managers["playlist_song_manager"], "playlist_song"),
        "▶️ Reproducciones": lambda: render_crud_tab(managers["reproduction_manager"], "reproduction")
    }

    selected_tab = st.sidebar.radio("Selecciona una pestaña:", list(tabs.keys()), key="sidebar_tab_selector")

    # Botón para cerrar sesión en la sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Cerrar Sesión y Volver a Iniciar", key="logout_button", use_container_width=True):
        logout()

    # Renderizar la pestaña seleccionada
    tabs[selected_tab]()

