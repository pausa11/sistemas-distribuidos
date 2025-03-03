import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from io import BytesIO
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
CORS(app)

# Configura la cadena de conexión a PostgreSQL mediante la variable de entorno
# Asegúrate de definir DATABASE_URL en el entorno de despliegue o usa la cadena por defecto.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo para almacenar los archivos (compartido por todos los computadores)
class BackupFile(Base):
    __tablename__ = "backup_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    backup_time = Column(DateTime, default=datetime.utcnow)

# Crear la tabla si aún no existe
Base.metadata.create_all(bind=engine)

@app.route('/replicate', methods=['POST'])
def replicate():
    """
    Endpoint donde el Primario envía el archivo para replicarlo.
    El archivo se guarda en la base de datos compartida.
    """
    if 'file' not in request.files:
        return "No file part in request", 400
    file = request.files['file']
    filename = request.form.get('filename', file.filename)
    if filename == '':
        return "No filename provided", 400

    try:
        file_data = file.read()
    except Exception as e:
        return f"Error al leer el archivo: {e}", 500

    session = SessionLocal()
    new_file = BackupFile(filename=filename, file_data=file_data)
    try:
        session.add(new_file)
        session.commit()
    except Exception as e:
        session.rollback()
        return f"Error al replicar el archivo '{filename}': {e}", 500
    finally:
        session.close()

    return f"Archivo '{filename}' replicado exitosamente en la base de datos.", 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Permite descargar un archivo almacenado en la base de datos compartida.
    """
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename).first()
    session.close()
    if backup_file:
        return send_file(BytesIO(backup_file.file_data), as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Archivo no encontrado"}), 404

@app.route('/files', methods=['GET'])
def list_files():
    """
    Devuelve la lista de nombres de archivos almacenados en la base de datos compartida.
    """
    session = SessionLocal()
    files = session.query(BackupFile).all()
    session.close()
    filenames = [file.filename for file in files]
    return jsonify(filenames)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    Permite eliminar un archivo almacenado en la base de datos compartida.
    """
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename).first()
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
