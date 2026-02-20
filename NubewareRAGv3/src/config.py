import mysql.connector
from mysql.connector import Error
import os

#CONFIGURACION DE LAS VARIABLES DE CONEXION DE LA DB DONDE IRAN ALOJADOS LOS CHROMAS RELACIONADOS A LOS DOCUMENTOS

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "liga_agil_user"),
        password=os.getenv("MYSQL_PASSWORD", "Nubeware2025."),
        database=os.getenv("MYSQL_DATABASE", "chroma_db")
    )