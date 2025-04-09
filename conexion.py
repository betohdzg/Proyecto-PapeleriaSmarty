
# conexion.py
import psycopg2

def get_db_connection():
    """
    Función para conectarse a la base de datos PostgreSQL.
    """
    conn = psycopg2.connect(
        host="192.168.137.154",
        port="5432",
        dbname="papeleriasmarty",
        user="postgres",
        password="roberto123"
    )
    return conn