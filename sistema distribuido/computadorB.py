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

# Cadenas de conexión para ambas bases de datos
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://sistemas_distribuidos_19ua_user:Qjs6iBx8Zr08xJ7Kg8N5dstODvNepO74@dpg-cv27unnnoe9s73auj4c0-a.oregon-postgres.render.com/sistemas_distribuidos_19ua"
)
DATABASE2_URL = os.environ.get(
    "DATABASE2_URL",
    "postgresql://sistema_distribuido_2_user:r7LwJZ3AGOXSgHmp9oaizJeMT6c7pGYR@dpg-cv2ufofnoe9s73bbblr0-a.oregon-postgres.render.com/sistema_distribuido_2"
)

# Configuración de SQLAlchemy para ambas conexiones
engine = create_engine(DATABASE_URL)
engine2 = create_engine(DATABASE2_URL)
SessionLocal = sessionmaker(bind=engine)
SessionLocal2 = sessionmaker(bind=engine2)
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

# Crear las tablas en ambas bases de datos
Base.metadata.create_all(bind=engine)
Base.metadata.create_all(bind=engine2)

# Endpoint para listar archivos de un usuario.
# Se intenta primero en la DB1 y si falla se consulta en la DB2.
@app.route('/files', methods=['GET'])
def list_files():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Parámetro user_id requerido"}), 400
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

# Endpoint para eliminar un archivo en ambas bases de datos.
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Parámetro user_id requerido"}), 400

    errors = []
    deleted_db1 = False
    deleted_db2 = False

    # Eliminación en DB1
    session = SessionLocal()
    backup_file_db1 = session.query(BackupFile).filter(
        BackupFile.filename == filename, BackupFile.user_id == int(user_id)
    ).first()
    if backup_file_db1:
        try:
            session.delete(backup_file_db1)
            session.commit()
            deleted_db1 = True
        except Exception as e:
            session.rollback()
            errors.append(f"Error eliminando en DB1: {e}")
        finally:
            session.close()
    else:
        session.close()
        errors.append("Archivo no encontrado en DB1")

    # Eliminación en DB2
    session2 = SessionLocal2()
    backup_file_db2 = session2.query(BackupFile).filter(
        BackupFile.filename == filename, BackupFile.user_id == int(user_id)
    ).first()
    if backup_file_db2:
        try:
            session2.delete(backup_file_db2)
            session2.commit()
            deleted_db2 = True
        except Exception as e:
            session2.rollback()
            errors.append(f"Error eliminando en DB2: {e}")
        finally:
            session2.close()
    else:
        session2.close()
        errors.append("Archivo no encontrado en DB2")

    if not deleted_db1 and not deleted_db2:
        return jsonify({"error": errors}), 404
    if errors:
        return jsonify({
            "message": f"Archivo '{filename}' eliminado en una o más bases, pero con errores.",
            "errors": errors
        }), 200
    return jsonify({"message": f"Archivo '{filename}' eliminado correctamente en ambas bases."}), 200

# Endpoint para descargar un archivo.
# Se intenta primero en la DB1 y, si no se encuentra, se consulta en la DB2.
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    session = SessionLocal()
    backup_file = session.query(BackupFile).filter(BackupFile.filename == filename).first()
    session.close()
    if not backup_file:
        session2 = SessionLocal2()
        backup_file = session2.query(BackupFile).filter(BackupFile.filename == filename).first()
        session2.close()
    if backup_file:
        return send_file(BytesIO(backup_file.file_data), as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "Archivo no encontrado"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
