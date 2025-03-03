import os
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos: define la variable de entorno DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua")

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo para almacenar los archivos en el primario
class BackupFile(Base):
    __tablename__ = "backup_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    backup_time = Column(DateTime, default=datetime.utcnow)

# Crear la tabla si no existe
Base.metadata.create_all(bind=engine)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Sube un archivo al Primario (almacenándolo en la base de datos) y lo replica al Server 2.
    El archivo se envía en la key 'file' (multipart/form-data).
    """
    if 'file' not in request.files:
        return "No file part in the request", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    try:
        # Leer el contenido del archivo como bytes
        file_data = file.read()
    except Exception as e:
        return f"Error al leer el archivo: {e}", 500

    # Guardar el archivo en la base de datos
    session = SessionLocal()
    new_file = BackupFile(filename=file.filename, file_data=file_data)
    try:
        session.add(new_file)
        session.commit()
    except Exception as e:
        session.rollback()
        return f"Error al guardar el archivo en la base de datos: {e}", 500
    finally:
        session.close()

    return f"Archivo '{file.filename}' subido y replicado correctamente.", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
