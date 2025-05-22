from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import bcrypt
from db import init_db
from models import User, db
import jwt
import datetime
import os 
from datetime import datetime, timedelta, timezone
from flask import make_response
app = Flask(__name__)
 
CORS(app, supports_credentials=True, origins="*")

# CORS (app, resources={r"/*": {"origins": "https://llama.cloudware.com.co/admin"}}, supports_credentials=True)
 
# CORS (app, resources={r"/*":{
#       "origins": "https://llama.cloudware.com.co",
#       "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#       "allow_headers": "*",
#       "supports_credentials": True
#       }})

 # LLama a la llave secreta de las variables de entorno
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Inicializar la base de datos
init_db(app)
 

@app.route('/')
def home():
    return jsonify({"message": "API conectada a PostgreSQL"}), 200
 

 
@app.route('/login', methods=['POST'])
def login():
    try:
        print("🔄 Recibiendo solicitud de login...")
 
        data = request.get_json()
        print("📦 Datos recibidos del cliente:", data)
 
        if not data or not data.get('email') or not data.get('password'):
            print("⚠️ Faltan campos obligatorios en el login")
            return jsonify({"error": "Faltan datos", "ok": False}), 400
 
        email = data['email']
        password = data['password']
        print(f"🔍 Buscando usuario con email: {email}")
 
        user = User.query.filter_by(email=email).first()
 
        if not user:
            print("❌ Usuario no encontrado")
            return jsonify({"message": "Usuario no encontrado", "ok": False}), 401
 
        print("✅ Usuario encontrado, validando contraseña...")
 
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            # Generar token JWT
            token = jwt.encode({
                'user_id': user.id,
                'role': user.role,
                'exp': datetime.now(timezone.utc) + timedelta(hours=8)
            }, app.config['SECRET_KEY'], algorithm='HS256')
 
            # Crear respuesta y guardar cookie
            response = make_response(jsonify({
                "ok": True,
                "message": "Inicio de sesión exitoso",
                "user": {
                    "email": user.email,
                    "role": user.role
                }
            }))
            response.set_cookie(
                key='access_token',
                value=token,
                httponly=True,
                secure=True,          # Solo funciona con HTTPS (usa False en local si es necesario)
                samesite='Lax',
                max_age=60*60*8       # 8 horas
            )
 
            return response
 
        else:
            return jsonify({"message": "Contraseña incorrecta", "ok": False}), 401
 
    except Exception as e:
        print("💥 Error:", str(e))
        return jsonify({"message": "Error interno del servidor", "ok": False}), 500


#REGISTRO DE USUARIOS
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print("📥 Datos recibidos:", data)
 
        required_fields = ['name', 'email', 'username', 'password', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({"ok": False, "message": "Faltan datos requeridos"}), 400
        
        #Verificar si el nombre de usuario es un email.
        if '@' in data['username']:
            return jsonify({"ok" : False, "message" : "El nombre de usuario no puede contener un '@'"})
 
        # Verificar si el email o username ya existen
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"ok": False, "message": "El email ya está registrado"}), 400
 
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"ok": False, "message": "El nombre de usuario ya está registrado"}), 400
 
        # Encriptar la contraseña
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
 
        # Crear el nuevo usuario
        new_user = User(
            name=data['name'],
            email=data['email'],
            username=data['username'],
            password=hashed_password.decode('utf-8'),  # Guardar como string
            role=data['role'],
            date_creation=datetime.utcnow()
        )
 
        db.session.add(new_user)
        db.session.commit()
 
        return jsonify({
            "ok": True,
            "message": "Usuario registrado exitosamente",
            "user": {
                "name": new_user.name,
                "email": new_user.email,
                "username": new_user.username,
                "role": new_user.role,
                "date_creation": new_user.date_creation.isoformat()
            }
        }), 201
 
    except Exception as e:
        print("❌ Error al registrar usuario:", str(e))
        return jsonify({"ok": False, "message": "Error interno del servidor"}), 500
 
 
@app.route('/users_list', methods=['GET'])
def get_all_users():
    try: 
        users = User.query.all()
        users_data = [user.serialize() for user in users]
        return jsonify({
                "ok" : True,
                "users" : users_data
            }), 200
    except Exception as e: 
        print("Error al obtener usuarios", str(e))
        return jsonify({
                    "ok" : False,
                    "message" : "Error interno del servidor"
                }), 500
 
#FUNCION DE LOGOUT
@app.route('/logout', methods=['POST'])
def logout():
    try:
        print("🚪 Cierre de sesión solicitado...")
 
        response = make_response(jsonify({"message": "Sesión cerrada", "ok": True}))
        response.set_cookie(
            key='access_token',
            value='',
            httponly=True,
            secure=True,  # Usa False en desarrollo local sin HTTPS
            samesite='Lax',
            max_age=0  # 🍪 Eliminar cookie
        )
        return response
    except Exception as e:
        print("💥 Error en logout:", str(e))
        return jsonify({"message": "Error cerrando sesión", "ok": False}), 500
 
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Servidor corriendo en http://localhost:{port}")
    app.run(debug=True, host="0.0.0.0", port=port)
 