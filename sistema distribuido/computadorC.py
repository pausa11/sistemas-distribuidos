import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos: define DATABASE_URL (asegúrate de configurarla en tu entorno de despliegue)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelo para almacenar los archivos (tabla compartida)
class BackupFile(Base):
    __tablename__ = "backup_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=False)  # En producción, podrías usar ForeignKey("users.id")

# Crear la tabla si aún no existe
Base.metadata.create_all(bind=engine)

@app.route('/files', methods=['GET'])
def list_files():
    """
    Lista los nombres de archivos asociados a un usuario.
    Se espera recibir el parámetro "user_id" en la query string.
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Se requiere el parámetro user_id"}), 400
    session = SessionLocal()
    files = session.query(BackupFile).filter(BackupFile.user_id == int(user_id)).all()
    session.close()
    filenames = [file.filename for file in files]
    return jsonify(filenames)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    Elimina un archivo asociado a un usuario.
    Se espera recibir el parámetro "user_id" en la query string para verificar la propiedad.
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Se requiere el parámetro user_id"}), 400
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename, BackupFile.user_id == int(user_id)).first()
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
    app.run(host="0.0.0.0", port=port)
