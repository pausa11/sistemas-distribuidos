import os
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configura la cadena de conexión a PostgreSQL mediante la variable de entorno
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BackupFile(Base):
    __tablename__ = "backup_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    backup_time = Column(DateTime, default=datetime.utcnow)

# Crear la tabla en la base de datos (si no existe)
Base.metadata.create_all(bind=engine)

@app.route('/files', methods=['GET'])
def list_backup_files():
    """
    Lista de archivos respaldados en la base de datos.
    Retorna un JSON con la lista de nombres de archivo.
    """
    session = SessionLocal()
    files = session.query(BackupFile).all()
    filenames = [file.filename for file in files]
    session.close()
    return jsonify(filenames)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_backup_file(filename):
    """
    Permite eliminar un archivo respaldado de la base de datos.
    """
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename).first()
    if backup_file:
        try:
            session.delete(backup_file)
            session.commit()
            return jsonify({"message": f"Archivo '{filename}' eliminado correctamente."}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"error": f"Error al eliminar el archivo: {e}"}), 500
        finally:
            session.close()
    else:
        session.close()
        return jsonify({"error": f"Archivo '{filename}' no encontrado."}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port)
