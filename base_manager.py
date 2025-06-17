from psycopg2 import sql
import streamlit as st # Importar streamlit para mensajes
from datetime import datetime, date
import datetime as dt # Importar datetime como dt para evitar conflictos con la clase datetime

class BaseManager:
    """
    Clase base para gestionar operaciones CRUD y paginación
    en una tabla específica de la base de datos.
    """
    def __init__(self, db_manager, table_name, columns, id_column):
        self.db_manager = db_manager
        self.table_name = table_name
        self.columns = columns # Diccionario de columnas {nombre_columna: tipo_db}
        self.id_column = id_column
        # Asegúrate de que las subclases definan 'foreign_key_columns' si las tienen
        self.foreign_key_columns = [] 

    def load_data_logic(self, tree_placeholder, pagination_info, page_label_placeholder, page_change=0, filter_column=None, filter_value=None):
        """
        Carga y muestra los datos de la tabla en el Treeview con paginación y filtro.
        Ahora soporta filtrar por múltiples IDs (números separados por comas).
        """
        new_offset = pagination_info["offset"] + page_change * pagination_info["limit"]

        # Inicializar where_clause como un objeto sql.SQL vacío
        where_clause = sql.SQL("")
        filter_params = []

        if filter_column and filter_value:
            col_type = self.columns.get(filter_column)
            
            # --- Lógica para filtrar múltiples IDs (ej. 1,2,3) ---
            if col_type == "INT" and ',' in str(filter_value):
                try:
                    # Dividir el string por comas y convertir a enteros
                    ids = [int(i.strip()) for i in filter_value.split(',') if i.strip().isdigit()]
                    if ids:
                        # Construir una cláusula IN con placeholders dinámicos
                        placeholders = sql.SQL(', ').join(sql.Placeholder() * len(ids))
                        where_clause = sql.SQL(" WHERE {} IN ({})").format(sql.Identifier(filter_column), placeholders)
                        filter_params = ids
                    else:
                        st.warning(f"Valores de ID inválidos en el filtro: '{filter_value}'. Se ignorará el filtro.")
                        filter_column = None # Ignorar el filtro si los IDs no son válidos
                except ValueError:
                    st.error(f"Error al procesar múltiples IDs. Asegúrate de que sean números separados por comas.")
                    filter_column = None # Ignorar el filtro
            # --- Lógica de filtro existente (para texto o un solo valor numérico) ---
            elif col_type == "TEXT":
                where_clause = sql.SQL(" WHERE {} ILIKE %s").format(sql.Identifier(filter_column))
                filter_params = [f"%{filter_value}%"]
            else: # Para un solo INT, BOOLEAN, DATE, TIME, TIMESTAMP
                where_clause = sql.SQL(" WHERE {} = %s").format(sql.Identifier(filter_column))
                try:
                    if col_type == "INT":
                        filter_params = [int(filter_value)]
                    elif col_type == "BOOLEAN":
                        filter_params = [filter_value.lower() == 'true']
                    elif col_type == "DATE":
                        # Aquí no hay strptime, el valor ya debería ser compatible
                        filter_params = [filter_value]
                    elif col_type == "TIME":
                        # Aquí no hay strptime, el valor ya debería ser compatible
                        filter_params = [filter_value]
                    elif col_type == "TIMESTAMP":
                        # Aquí no hay strptime, el valor ya debería ser compatible
                        filter_params = [filter_value]
                    else: # Cualquier otro tipo de TEXT no manejado por ILIKE
                        filter_params = [filter_value]
                except ValueError:
                    st.error(f"Valor de filtro inválido para la columna '{filter_column.replace('_', ' ').title()}'. Asegúrate de que el tipo de dato sea correcto.")
                    return # No ejecutar la consulta si el valor es inválido

        count_query_template = sql.SQL("SELECT COUNT(*) FROM {} {}").format(
            sql.Identifier(self.table_name),
            where_clause
        )
        total_records_result = self.db_manager.execute_query(count_query_template, filter_params, fetch_type='one')
        if total_records_result:
            pagination_info["total_records"] = total_records_result[0]
        else:
            pagination_info["total_records"] = 0

        max_offset = max(0, pagination_info["total_records"] - pagination_info["limit"])
        new_offset = max(0, min(new_offset, max_offset))

        if page_change != 0 and new_offset == pagination_info["offset"] and pagination_info["total_records"] > 0:
            st.info("Ya estás en la primera/última página.")
            return

        pagination_info["offset"] = new_offset
        pagination_info["current_page"] = (pagination_info["offset"] // pagination_info["limit"]) + 1

        # Actualizar el placeholder de la etiqueta de página
        with page_label_placeholder.container():
            st.write(f"Página {pagination_info['current_page']} de { (pagination_info['total_records'] + pagination_info['limit'] - 1) // pagination_info['limit'] }")


        # Definir main_query_template SIEMPRE antes de su uso
        main_query_template = sql.SQL("SELECT {} FROM {} {} ORDER BY {} LIMIT %s OFFSET %s").format(
            sql.SQL(',').join(map(sql.Identifier, self.columns.keys())),
            sql.Identifier(self.table_name),
            where_clause, # Ahora where_clause siempre es un objeto sql.SQL
            sql.Identifier(self.id_column)
        )
        query_params = filter_params + [pagination_info["limit"], pagination_info["offset"]]
        data = self.db_manager.execute_query(main_query_template, tuple(query_params), fetch_type='all')

        # Convertir a formato de DataFrame para Streamlit
        import pandas as pd
        if data:
            df = pd.DataFrame(data, columns=self.columns.keys())
            # Formatear fechas/tiempos en el DataFrame para una mejor visualización
            for col_name, col_type in self.columns.items():
                if col_type == "DATE" and col_name in df.columns:
                    df[col_name] = df[col_name].apply(lambda x: x.strftime("%Y-%m-%d") if isinstance(x, (datetime, date)) else '')
                elif col_type == "TIME" and col_name in df.columns:
                    df[col_name] = df[col_name].apply(lambda x: x.strftime("%H:%M:%S") if isinstance(x, dt.time) else (str(x) if x else ''))
                elif col_type == "TIMESTAMP" and col_name in df.columns:
                    df[col_name] = df[col_name].dt.strftime("%Y-%m-%d %H:%M:%S").fillna('')
                elif col_type == "BOOLEAN" and col_name in df.columns:
                     df[col_name] = df[col_name].apply(lambda x: 'True' if x else ('False' if x is False else ''))

            with tree_placeholder.container():
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            with tree_placeholder.container():
                st.info("No hay datos para mostrar.")
            

    def create_record_logic(self, entry_values):
        """
        Crea un nuevo registro en la tabla.
        :param entry_values: Diccionario de valores de entrada desde st.session_state.
        """
        values = []
        col_names = []
        for col_name, col_type in self.columns.items():
            if col_name == self.id_column:
                continue
            value = entry_values.get(col_name) # Obtener valor del diccionario
            
            # --- CORRECCIÓN AQUÍ: No usar strptime si ya es un objeto de fecha/hora ---
            try:
                if col_type == "INT":
                    values.append(int(value) if value is not None and value != '' else None)
                elif col_type == "BOOLEAN":
                    if isinstance(value, bool): values.append(value) # Ya es bool de st.checkbox
                    elif str(value).lower() == 'true': values.append(True)
                    elif str(value).lower() == 'false': values.append(False)
                    else: values.append(None)
                elif col_type == "DATE":
                    # Si el valor ya es un objeto date (de st.date_input), úsalo directamente.
                    # Si es una cadena (ej. de text_input), entonces sí parsea.
                    if isinstance(value, date):
                        values.append(value)
                    elif isinstance(value, str) and value:
                        values.append(datetime.strptime(value, '%Y-%m-%d').date())
                    else:
                        values.append(None)
                elif col_type == "TIME":
                    # Si el valor ya es un objeto time, úsalo directamente.
                    if isinstance(value, dt.time): # Usar dt.time para comparar
                        values.append(value)
                    elif isinstance(value, str) and value:
                        values.append(datetime.strptime(value, '%H:%M:%S').time())
                    else:
                        values.append(None)
                elif col_type == "TIMESTAMP":
                    # Si el valor ya es un objeto datetime, úsalo directamente.
                    if isinstance(value, datetime):
                        values.append(value)
                    elif isinstance(value, str) and value:
                        values.append(datetime.strptime(value, '%Y-%m-%d %H:%M:%S'))
                    else:
                        values.append(None)
                else: # TEXT
                    values.append(value if value is not None and value != '' else None)
                
                col_names.append(col_name)
            except ValueError:
                st.error(f"Valor inválido para el campo '{col_name.replace('_', ' ').title()}'. Asegúrate de que el tipo de dato sea correcto.")
                return False

        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING {}").format(
            sql.Identifier(self.table_name),
            sql.SQL(', ').join(map(sql.Identifier, col_names)),
            sql.SQL(', ').join(sql.Placeholder() * len(col_names)),
            sql.Identifier(self.id_column)
        )
        new_id = self.db_manager.execute_query(insert_query, tuple(values), fetch_type='one')
        if new_id:
            st.success(f"Registro creado con ID: {new_id[0]}")
            return True
        return False

    def load_selected_record_logic(self, selected_id):
        """
        Carga el registro seleccionado.
        :param selected_id: ID del registro a cargar.
        :return: Diccionario con los valores del registro o None.
        """
        if not selected_id:
            st.warning("Por favor, introduce el ID del registro para cargar.")
            return None
        try:
            selected_id = int(selected_id)
        except ValueError:
            st.error("El ID debe ser un número entero.")
            return None

        query = sql.SQL("SELECT {} FROM {} WHERE {} = %s").format(
            sql.SQL(',').join(map(sql.Identifier, self.columns.keys())),
            sql.Identifier(self.table_name),
            sql.Identifier(self.id_column)
        )
        record = self.db_manager.execute_query(query, (selected_id,), fetch_type='one')

        if record:
            record_dict = {}
            for i, col_name in enumerate(self.columns.keys()):
                value = record[i]
                # Formatear valores para mostrarlos en los campos de entrada de Streamlit
                if isinstance(value, datetime):
                     if self.columns[col_name] == "DATE":
                         record_dict[col_name] = value.strftime("%Y-%m-%d")
                     elif self.columns[col_name] == "TIME":
                         record_dict[col_name] = value.strftime("%H:%M:%S")
                     else: # TIMESTAMP
                         record_dict[col_name] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, date):
                     record_dict[col_name] = value.strftime("%Y-%m-%d")
                elif isinstance(value, bool):
                     record_dict[col_name] = value # st.checkbox maneja bool directamente
                else:
                    record_dict[col_name] = value
            return record_dict
        else:
            st.error(f"No se encontró ningún registro con ID: {selected_id}")
            return None

    def update_record_logic(self, entry_values):
        """
        Actualiza un registro existente en la tabla.
        Ahora solo actualiza los campos que están presentes en entry_values,
        preservando los valores de los campos no incluidos (como las FKs no mostradas).
        :param entry_values: Diccionario de valores de entrada desde st.session_state
                             (contiene solo los campos visibles/editables).
        """
        id_value_str = entry_values.get(self.id_column)
        if not id_value_str:
            st.error(f"Por favor, introduce el ID del {self.table_name} a actualizar.")
            return False

        try:
            id_value = int(id_value_str)
        except ValueError:
            st.error("El ID debe ser un número entero.")
            return False

        set_clauses = []
        params = []
        
        # Iterar sobre los campos que se proporcionaron desde la interfaz
        for col_name, value in entry_values.items():
            if col_name == self.id_column: # El ID de la tabla actual se usa para el WHERE, no para SET
                continue 

            col_type = self.columns.get(col_name) # Obtener el tipo de la columna desde la definición completa
            if col_type is None: # Si por alguna razón el campo no está en self.columns, lo ignoramos
                continue

            # --- CORRECCIÓN AQUÍ: No usar strptime si ya es un objeto de fecha/hora ---
            if value == '' or value is None: # Si el campo está vacío o es None
                if col_type in ["BOOLEAN", "DATE", "TIME", "TIMESTAMP", "INT", "TEXT"]:
                    set_clauses.append(sql.SQL("{} = NULL").format(sql.Identifier(col_name)))
                else: # Para otros tipos no nulos (ej. si fueras a permitir VARCHAR(x) NOT NULL sin default)
                    params.append(value)
                    set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(col_name)))
            else:
                try:
                    if col_type == "INT":
                        params.append(int(value))
                    elif col_type == "BOOLEAN":
                        params.append(bool(value)) # Convertir a booleano
                    elif col_type == "DATE":
                        # Si el valor ya es un objeto date (de st.date_input), úsalo directamente.
                        # Si es una cadena (ej. de text_input), entonces sí parsea.
                        if isinstance(value, date):
                            params.append(value)
                        elif isinstance(value, str):
                            params.append(datetime.strptime(value, '%Y-%m-%d').date())
                        else:
                            params.append(None)
                    elif col_type == "TIME":
                        # Si el valor ya es un objeto time, úsalo directamente.
                        if isinstance(value, dt.time):
                            params.append(value)
                        elif isinstance(value, str):
                            params.append(datetime.strptime(value, '%H:%M:%S').time())
                        else:
                            params.append(None)
                    elif col_type == "TIMESTAMP":
                        # Si el valor ya es un objeto datetime, úsalo directamente.
                        if isinstance(value, datetime):
                            params.append(value)
                        elif isinstance(value, str):
                            params.append(datetime.strptime(value, '%Y-%m-%d %H:%M:%S'))
                        else:
                            params.append(None)
                    else: # TEXT
                        params.append(value)
                    set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(col_name)))
                except ValueError:
                    st.error(f"Valor inválido para el campo '{col_name.replace('_', ' ').title()}'. Asegúrate de que el tipo de dato sea correcto.")
                    return False

        if not set_clauses:
            st.info("No hay campos para actualizar.")
            return False

        params.append(id_value)
        update_query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
            sql.Identifier(self.table_name),
            sql.SQL(', ').join(set_clauses),
            sql.Identifier(self.id_column)
        )
        self.db_manager.execute_query(update_query, tuple(params))
        st.success(f"Registro de {self.table_name} actualizado correctamente.")
        return True

    def delete_record_logic(self, id_value):
        """
        Elimina un registro de la tabla especificada.
        :param id_value: ID del registro a eliminar.
        """
        if not id_value:
            st.error(f"Por favor, introduce el ID del {self.table_name} a eliminar.")
            return False

        try:
            id_value = int(id_value)
        except ValueError:
            st.error("El ID debe ser un número entero.")
            return False

        delete_query = sql.SQL("DELETE FROM {} WHERE {} = %s").format(
            sql.Identifier(self.table_name),
            sql.Identifier(self.id_column)
        )
        self.db_manager.execute_query(delete_query, (id_value,))
        st.success(f"Registro de {self.table_name} eliminado correctamente.")
        return True

