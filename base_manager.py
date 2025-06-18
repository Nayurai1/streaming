from psycopg2 import sql
import streamlit as st
from datetime import datetime, date, time # Importar time explícitamente

class BaseManager:
    """
    Clase base para gestionar operaciones CRUD y paginación
    en una tabla específica de la base de datos para Streamlit.
    """
    def __init__(self, db_manager, table_name, columns, id_column):
        self.db_manager = db_manager
        self.table_name = table_name
        self.columns = columns # Diccionario de columnas {nombre_columna: tipo_db}
        self.id_column = id_column

    def load_data_logic(self, table_placeholder, pagination_info, page_label_placeholder, page_change=0, filter_column=None, filter_value=None):
        """
        Carga y muestra los datos de la tabla en un st.dataframe con paginación y filtro.
        """
        new_offset = pagination_info["offset"] + page_change * pagination_info["limit"]

        where_clause = sql.SQL("")
        filter_params = []

        if filter_column and filter_value:
            col_type = self.columns.get(filter_column)
            
            # Lógica para filtrar múltiples IDs (ej. 1,2,3) o valores de texto/número
            if col_type == "INT" and ',' in str(filter_value):
                try:
                    ids = [int(i.strip()) for i in filter_value.split(',') if i.strip().isdigit()]
                    if ids:
                        placeholders = sql.SQL(', ').join(sql.Placeholder() * len(ids))
                        where_clause = sql.SQL(" WHERE {} IN ({})").format(sql.Identifier(filter_column), placeholders)
                        filter_params = ids
                    else:
                        st.warning(f"Valores de ID inválidos en el filtro: '{filter_value}'. Se ignorará el filtro.")
                        filter_column = None
                except ValueError:
                    st.error(f"Error al procesar múltiples IDs. Asegúrate de que sean números separados por comas.")
                    filter_column = None
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
                        filter_params = [datetime.strptime(filter_value, "%Y-%m-%d").date()]
                    elif col_type == "TIME":
                        filter_params = [datetime.strptime(filter_value, "%H:%M:%S").time()]
                    elif col_type == "TIMESTAMP":
                        filter_params = [datetime.strptime(filter_value, "%Y-%m-%d %H:%M:%S")]
                    else:
                        filter_params = [filter_value]
                except ValueError:
                    st.error(f"Valor de filtro inválido para la columna '{filter_column.replace('_', ' ').title()}'. Asegúrate de que el tipo de dato sea correcto.")
                    # No retornar, solo advertir y continuar sin aplicar este filtro inválido
                    filter_column = None # Resetear el filtro para no fallar la consulta principal


        # Volver a calcular total_records con el filtro aplicado
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
        with page_label_placeholder:
            total_pages = (pagination_info['total_records'] + pagination_info['limit'] - 1) // pagination_info['limit']
            st.write(f"Página {pagination_info['current_page']} de {total_pages if total_pages > 0 else 1}")

        # Definir main_query_template SIEMPRE antes de su uso
        main_query_template = sql.SQL("SELECT {} FROM {} {} ORDER BY {} LIMIT %s OFFSET %s").format(
            sql.SQL(',').join(map(sql.Identifier, self.columns.keys())),
            sql.Identifier(self.table_name),
            where_clause,
            sql.Identifier(self.id_column)
        )
        query_params = filter_params + [pagination_info["limit"], pagination_info["offset"]]
        data = self.db_manager.execute_query(main_query_template, tuple(query_params), fetch_type='all')

        import pandas as pd
        if data:
            df = pd.DataFrame(data, columns=self.columns.keys())
            # Formatear fechas/tiempos en el DataFrame para una mejor visualización
            for col_name, col_type in self.columns.items():
                if col_type == "DATE" and col_name in df.columns:
                    df[col_name] = df[col_name].apply(lambda x: x.strftime("%Y-%m-%d") if isinstance(x, (datetime, date)) else None)
                elif col_type == "TIME" and col_name in df.columns:
                    df[col_name] = df[col_name].apply(lambda x: str(x) if isinstance(x, time) else None)
                elif col_type == "TIMESTAMP" and col_name in df.columns:
                    df[col_name] = df[col_name].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, datetime) else None)
                elif col_type == "BOOLEAN" and col_name in df.columns:
                     df[col_name] = df[col_name].apply(lambda x: 'True' if x else ('False' if x is False else None))

            with table_placeholder: # Usar el placeholder para actualizar
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            with table_placeholder: # Usar el placeholder para actualizar
                st.info("No hay datos para mostrar.")
            
            # Si no hay datos, asegurarse de que la paginación refleje esto
            pagination_info["total_records"] = 0
            with page_label_placeholder:
                st.write(f"Página 0 de 0")


    def create_record_logic(self, form_data):
        """
        Crea un nuevo registro en la tabla.
        :param form_data: Diccionario de valores de entrada desde el formulario de Streamlit.
        """
        values = []
        col_names = []
        for col_name, col_type in self.columns.items():
            if col_name == self.id_column: # El ID es SERIAL, no se inserta manualmente
                continue

            value = form_data.get(col_name)
            
            # Conversión de tipos basada en el esquema de la base de datos
            try:
                if col_type == "INT":
                    # Si el valor es None o '', se convierte a None (NULL en DB)
                    values.append(int(value) if value is not None and value != '' else None)
                elif col_type == "BOOLEAN":
                    values.append(bool(value) if value is not None else None) # st.checkbox ya devuelve bool
                elif col_type == "DATE":
                    # st.date_input ya devuelve un objeto date o None
                    values.append(value if isinstance(value, date) else None)
                elif col_type == "TIME":
                    # st.text_input para TIME, convertir de string a time object
                    values.append(datetime.strptime(value, '%H:%M:%S').time() if value else None)
                elif col_type == "TIMESTAMP":
                    # st.text_input para TIMESTAMP, convertir de string a datetime object
                    values.append(datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value else None)
                else: # TEXT
                    values.append(value if value is not None and value != '' else None)
                
                col_names.append(col_name)
            except ValueError:
                st.error(f"Error en el formato del campo '{col_name.replace('_', ' ').title()}'.")
                return False # Detener la operación si hay error de tipo
            except Exception as e:
                st.error(f"Error inesperado procesando '{col_name.replace('_', ' ').title()}': {e}")
                return False

        if not col_names: # No hay columnas para insertar (ej. solo el ID estaba en el formulario)
            st.warning("No hay datos válidos para crear el registro.")
            return False

        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING {}").format(
            sql.Identifier(self.table_name),
            sql.SQL(', ').join(map(sql.Identifier, col_names)),
            sql.SQL(', ').join(sql.Placeholder() * len(col_names)),
            sql.Identifier(self.id_column)
        )
        
        new_id = self.db_manager.execute_query(insert_query, tuple(values), fetch_type='one')
        if new_id:
            st.success(f"Registro de {self.table_name} creado con ID: {new_id[0]}")
            return True
        return False

    def load_selected_record_logic(self, selected_id_str):
        """
        Carga el registro seleccionado en los campos del formulario.
        :param selected_id_str: ID del registro a cargar (como string del input).
        :return: Diccionario con los valores del registro o None.
        """
        if not selected_id_str:
            st.warning("Por favor, introduce el ID del registro para cargar.")
            return None
        try:
            selected_id = int(selected_id_str)
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
                # Convertir valores de la BD a un formato adecuado para los widgets de Streamlit
                if self.columns[col_name] == "DATE":
                    record_dict[col_name] = value.strftime("%Y-%m-%d") if isinstance(value, date) else ""
                elif self.columns[col_name] == "TIME":
                    record_dict[col_name] = str(value) if isinstance(value, time) else ""
                elif self.columns[col_name] == "TIMESTAMP":
                    record_dict[col_name] = value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else ""
                elif self.columns[col_name] == "BOOLEAN":
                    record_dict[col_name] = value # st.checkbox maneja bool directamente
                else:
                    record_dict[col_name] = value
            record_dict[self.id_column] = selected_id_str # Asegurar que el ID se mantenga en el formulario
            return record_dict
        else:
            st.error(f"No se encontró ningún registro con ID: {selected_id}")
            return None


    def update_record_logic(self, form_data):
        """
        Actualiza un registro existente en la tabla.
        :param form_data: Diccionario de valores de entrada desde el formulario de Streamlit.
        """
        id_value_str = form_data.get(self.id_column)
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
        
        for col_name, col_type in self.columns.items():
            if col_name == self.id_column:
                continue

            value = form_data.get(col_name) # Obtener el valor del formulario

            # Construir cláusulas SET y parámetros dinámicamente
            try:
                if col_type == "INT":
                    params.append(int(value) if value is not None and value != '' else None)
                elif col_type == "BOOLEAN":
                    params.append(bool(value) if value is not None else None)
                elif col_type == "DATE":
                    params.append(value if isinstance(value, date) else None)
                elif col_type == "TIME":
                    params.append(datetime.strptime(value, '%H:%M:%S').time() if value else None)
                elif col_type == "TIMESTAMP":
                    params.append(datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if value else None)
                else: # TEXT
                    params.append(value if value is not None and value != '' else None)
                
                set_clauses.append(sql.SQL("{} = %s").format(sql.Identifier(col_name)))
            except ValueError:
                st.error(f"Error en el formato del campo '{col_name.replace('_', ' ').title()}'.")
                return False
            except Exception as e:
                st.error(f"Error inesperado procesando '{col_name.replace('_', ' ').title()}': {e}")
                return False


        if not set_clauses:
            st.info("No hay campos para actualizar.")
            return False

        params.append(id_value) # El ID va al final para la cláusula WHERE

        update_query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
            sql.Identifier(self.table_name),
            sql.SQL(', ').join(set_clauses),
            sql.Identifier(self.id_column)
        )
        self.db_manager.execute_query(update_query, tuple(params))
        st.success(f"Registro de {self.table_name} actualizado correctamente.")
        return True


    def delete_record_logic(self, id_value_str):
        """
        Elimina un registro de la tabla especificada.
        :param id_value_str: ID del registro a eliminar (como string del input).
        """
        if not id_value_str:
            st.error(f"Por favor, introduce el ID del {self.table_name} a eliminar.")
            return False

        try:
            id_value = int(id_value_str)
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

