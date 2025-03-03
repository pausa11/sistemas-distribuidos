import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos: define la variable de entorno DATABASE_URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo de usuario
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    files = relationship("BackupFile", back_populates="owner")

# Modelo para almacenar los archivos (compartido por todos los computadores)
class BackupFile(Base):
    __tablename__ = "backup_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="files")

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

# Endpoint de registro
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    session = SessionLocal()
    # Verificar si el usuario ya existe
    existing_user = session.query(User).filter(User.username == username).first()
    if existing_user:
        session.close()
        return jsonify({"error": "Username already exists"}), 400
    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash)
    session.add(new_user)
    session.commit()
    session.close()
    return jsonify({"message": "User registered successfully"}), 201

# Endpoint de login
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401
    # Para un login sencillo, devolvemos el ID del usuario. En producción, usar tokens JWT.
    return jsonify({"message": "Login successful", "user_id": user.id}), 200

# Endpoint para subir archivos asociados a un usuario
@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Sube un archivo al Primario (almacenándolo en la base de datos) y lo replica a otro servidor.
    Se espera que el formulario incluya además un campo "user_id" para asociar el archivo.
    """
    if 'file' not in request.files:
        return "No file part in the request", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    user_id = request.form.get("user_id")
    if not user_id:
        return "No user specified", 400

    try:
        file_data = file.read()
    except Exception as e:
        return f"Error al leer el archivo: {e}", 500

    session = SessionLocal()
    new_file = BackupFile(filename=file.filename, file_data=file_data, user_id=int(user_id))
    try:
        session.add(new_file)
        session.commit()
    except Exception as e:
        session.rollback()
        return f"Error al guardar el archivo en la base de datos: {e}", 500
    finally:
        session.close()

    # Aquí podrías replicar el archivo a otro servidor usando requests.post si es necesario
    return f"Archivo '{file.filename}' subido correctamente", 201

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
