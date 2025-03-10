import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuración de las bases de datos
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)
DATABASE2_URL = os.environ.get(
    "DATABASE2_URL",
    "postgresql://sistema_distribuido_2_user:r7LwJZ3AGOXSgHmp9oaizJeMT6c7pGYR@dpg-cv2ufofnoe9s73bbblr0-a.oregon-postgres.render.com/sistema_distribuido_2"
)

# Motores y sesiones para ambas bases de datos
engine = create_engine(DATABASE_URL)
engine2 = create_engine(DATABASE2_URL)
SessionLocal = sessionmaker(bind=engine)
SessionLocal2 = sessionmaker(bind=engine2)
Base = declarative_base()

# Modelo para almacenar los archivos
class BackupFile(Base):
    __tablename__ = "backup_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=False)  # En producción, podrías usar ForeignKey("users.id")

# Crear la tabla en ambas bases de datos si aún no existe
Base.metadata.create_all(bind=engine)
Base.metadata.create_all(bind=engine2)

@app.route('/files', methods=['GET'])
def list_files():
    """
    Lista los nombres de archivos asociados a un usuario.
    Primero se intenta consultar la DB primaria; si ocurre algún error (por ejemplo, la DB no responde),
    se realiza la consulta en la DB secundaria.
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Se requiere el parámetro user_id"}), 400
    
    # Intentar en DB1
    try:
        session = SessionLocal()
        files = session.query(BackupFile).filter(BackupFile.user_id == int(user_id)).all()
        session.close()
        filenames = [file.filename for file in files]
        return jsonify(filenames)
    except Exception as e:
        # Si ocurre un error con DB1, se intenta con DB2
        try:
            session2 = SessionLocal2()
            files = session2.query(BackupFile).filter(BackupFile.user_id == int(user_id)).all()
            session2.close()
            filenames = [file.filename for file in files]
            return jsonify(filenames)
        except Exception as e2:
            return jsonify({"error": "Error al obtener archivos de ambas bases de datos"}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    Elimina un archivo asociado a un usuario en ambas bases de datos.
    Se espera recibir el parámetro "user_id" en la query string para verificar la propiedad.
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Se requiere el parámetro user_id"}), 400

    errors = []
    deleted_db1 = False
    deleted_db2 = False

    # Eliminación en DB1
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(
        BackupFile.filename == filename, BackupFile.user_id == int(user_id)
    ).first()
    if backup_file:
        try:
            session.delete(backup_file)
            session.commit()
            deleted_db1 = True
        except Exception as e:
            session.rollback()
            errors.append(f"Error eliminando en DB1: {str(e)}")
    session.close()

    # Eliminación en DB2
    session2 = SessionLocal2()
    backup_file2 = session2.query(BackupFile).filter(
        BackupFile.filename == filename, BackupFile.user_id == int(user_id)
    ).first()
    if backup_file2:
        try:
            session2.delete(backup_file2)
            session2.commit()
            deleted_db2 = True
        except Exception as e:
            session2.rollback()
            errors.append(f"Error eliminando en DB2: {str(e)}")
    session2.close()

    # Si el archivo no se encontró en ninguna de las dos bases, se informa el error.
    if not deleted_db1 and not deleted_db2:
        errors.append(f"Archivo '{filename}' no encontrado en ninguna de las bases de datos.")
    
    if errors:
        return jsonify({"error": errors}), 500

    return jsonify({"message": f"Archivo '{filename}' eliminado correctamente en ambas bases de datos."}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
