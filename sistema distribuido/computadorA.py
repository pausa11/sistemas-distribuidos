import os
from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Carpeta donde almacenamos los archivos subidos en el Primario
PRIMARY_STORAGE = "./data_primary"
os.makedirs(PRIMARY_STORAGE, exist_ok=True)

# Sustituir por la IP o hostname y puerto del Server 2 (Réplica)
REPLICA_URL = "https://maquina-b.onrender.com"

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Sube un archivo al Primario y luego lo replica al Server 2.
    Envía el archivo en la key 'file' (multipart/form-data).
    """
    if 'file' not in request.files:
        return "No file part in the request", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # Guardar el archivo localmente
    filepath = os.path.join(PRIMARY_STORAGE, file.filename)
    file.save(filepath)

    # Replicar el archivo al Server 2
    try:
        with open(filepath, 'rb') as f:
            requests.post(
                f"{REPLICA_URL}/replicate",
                files={'file': (file.filename, f, file.content_type)},
                data={'filename': file.filename}  # Para conservar el nombre
            )
    except Exception as e:
        print(f"Error al replicar archivo {file.filename}: {e}")

    return f"Archivo '{file.filename}' subido y replicado correctamente.", 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Permite descargar un archivo alojado en el Primario.
    """
    return send_from_directory(PRIMARY_STORAGE, filename, as_attachment=True)

@app.route('/files', methods=['GET'])
def list_files():
    """
    Devuelve la lista de archivos almacenados en el Primario.
    """
    files = os.listdir(PRIMARY_STORAGE)
    return jsonify(files)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    Permite eliminar un archivo almacenado en el Primario.
    """
    filepath = os.path.join(PRIMARY_STORAGE, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            # Opcional: replicar la eliminación al servidor réplica
            try:
                requests.delete(f"{REPLICA_URL}/delete/{filename}")
            except Exception as e:
                print(f"Error al replicar la eliminación del archivo {filename}: {e}")
            return f"Archivo '{filename}' eliminado correctamente.", 200
        except Exception as e:
            return f"Error al eliminar el archivo '{filename}': {e}", 500
    else:
        return f"Archivo '{filename}' no encontrado.", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
