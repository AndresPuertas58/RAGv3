# db.py - Gestión de la conexión a la base de datos
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
 
# Cargar variables de entorno
load_dotenv()
 
# Crear instancia de SQLAlchemy
db = SQLAlchemy()
 
def get_database_url():
    """Obtener la URL de conexión a la base de datos desde variables de entorno"""
    return (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
 
def init_db(app):
    """Configura e inicializa la conexión a la base de datos"""
    # Configurar conexión a PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   
    # Inicializar DB con la aplicación
    db.init_app(app)
   
    # Crear todas las tablas si no existen
    with app.app_context():
        db.create_all()
        print("✅ Base de datos inicializada correctamente")