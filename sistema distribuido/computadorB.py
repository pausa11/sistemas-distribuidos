import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from io import BytesIO
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

app = Flask(__name__)
CORS(app)

# Configura la cadena de conexión a PostgreSQL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo de Usuario
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    files = relationship("BackupFile", back_populates="owner")

# Modelo para almacenar los archivos (tabla compartida)
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

# Endpoint para replicar archivos (operación de subida)
# Se espera que el formulario incluya "user_id" para asociar el archivo a un usuario.
@app.route('/replicate', methods=['POST'])
def replicate():
    if 'file' not in request.files:
        return "No file part in request", 400
    file = request.files['file']
    filename = request.form.get('filename', file.filename)
    if filename == '':
        return "No filename provided", 400
    user_id = request.form.get("user_id")
    if not user_id:
        return "No user specified", 400

    try:
        file_data = file.read()
    except Exception as e:
        return f"Error al leer el archivo: {e}", 500

    session = SessionLocal()
    new_file = BackupFile(filename=filename, file_data=file_data, user_id=int(user_id))
    try:
        session.add(new_file)
        session.commit()
    except Exception as e:
        session.rollback()
        return f"Error al replicar el archivo '{filename}': {e}", 500
    finally:
        session.close()

    return f"Archivo '{filename}' replicado exitosamente en la base de datos.", 200

# Endpoint para descargar archivos.
# Nota: En este ejemplo no se filtra por usuario para la descarga; en un entorno real, podrías agregar comprobaciones.
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename).first()
    session.close()
    if backup_file:
        return send_file(BytesIO(backup_file.file_data), as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Archivo no encontrado"}), 404

# Endpoint para listar archivos de un usuario.
# Se espera recibir el parámetro "user_id" en la query string.
@app.route('/files', methods=['GET'])
def list_files():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Parámetro user_id requerido"}), 400
    session = SessionLocal()
    files = session.query(BackupFile).filter(BackupFile.user_id == int(user_id)).all()
    session.close()
    filenames = [file.filename for file in files]
    return jsonify(filenames)

# Endpoint para eliminar un archivo.
# Se espera que se reciba el parámetro "user_id" en la query string para comprobar la propiedad del archivo.
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Parámetro user_id requerido"}), 400
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename, BackupFile.user_id == int(user_id)).first()
    if backup_file:
        try:
            session.delete(backup_file)
            session.commit()
            return f"Archivo '{filename}' eliminado exitosamente.", 200
        except Exception as e:
            session.rollback()
            return f"Error al eliminar el archivo '{filename}': {e}", 500
        finally:
            session.close()
    else:
        session.close()
        return f"Archivo '{filename}' no encontrado.", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
