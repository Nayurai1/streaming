import psycopg2

# --- Configura tus datos de conexión aquí ---
DB_NAME = "plataforma_streaming"
DB_USER = "postgres"
DB_PASSWORD = "123456" # <--- ¡Asegúrate de que esta sea tu contraseña real de PostgreSQL!
DB_HOST = "localhost"
DB_PORT = "5432"

def test_postgresql_connection():
    """
    Intenta conectarse a la base de datos PostgreSQL y reporta el resultado.
    """
    print(f"Intentando conectar a la base de datos PostgreSQL:")
    print(f"  Base de datos: {DB_NAME}")
    print(f"  Usuario: {DB_USER}")
    print(f"  Host: {DB_HOST}")
    print(f"  Puerto: {DB_PORT}")
    print(f"  Contraseña: {'********' if DB_PASSWORD else '[Vacía]'}") # No mostrar la contraseña real por seguridad

    conn = None
    try:
        # Intenta establecer la conexión
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            client_encoding='UTF8' # Importante para manejar caracteres especiales
        )
        print("\n¡Conexión a la base de datos PostgreSQL exitosa!")

        # Opcional: Ejecutar una consulta simple para verificar que todo funciona
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Versión de PostgreSQL: {db_version[0]}")

        cursor.close()

    except psycopg2.OperationalError as e:
        print(f"\n¡ERROR DE CONEXIÓN! No se pudo conectar a la base de datos.")
        print(f"Detalles del error: {e}")
        print("\nPosibles causas:")
        print("1. El servidor PostgreSQL no está en ejecución. Asegúrate de iniciarlo.")
        print("2. Las credenciales (usuario, contraseña, host, puerto, nombre de la BD) son incorrectas.")
        print("3. La base de datos 'plataforma_streaming' no existe o no está bien configurada.")
        print("4. Un firewall está bloqueando la conexión al puerto 5432.")
    except Exception as e:
        print(f"\nSe produjo un error inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("\nConexión a la base de datos cerrada.")

if __name__ == "__main__":
    test_postgresql_connection()
