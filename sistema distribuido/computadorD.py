import os
from flask import Flask, jsonify, send_file
from flask_cors import CORS
from io import BytesIO
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos: asegúrate de definir la variable de entorno DATABASE_URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)

# Configuración de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo para almacenar los archivos de respaldo en la base de datos
class BackupFile(Base):
    __tablename__ = "backup_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    backup_time = Column(DateTime, default=datetime.utcnow)

# Crear la tabla si aún no existe
Base.metadata.create_all(bind=engine)

@app.route('/download/<filename>', methods=['GET'])
def download_backup_file(filename):
    """
    Permite descargar un archivo respaldado consultándolo en la base de datos.
    """
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename).first()
    session.close()
    if backup_file:
        return send_file(BytesIO(backup_file.file_data), as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Archivo no encontrado"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(host='0.0.0.0', port=port)
