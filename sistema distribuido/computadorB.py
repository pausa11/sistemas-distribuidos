import os
from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Carpeta donde almacenamos los archivos que recibimos del Primario
REPLICA_STORAGE = "./data_replica"
os.makedirs(REPLICA_STORAGE, exist_ok=True)

@app.route('/replicate', methods=['POST'])
def replicate():
    """
    Endpoint donde el Primario envía el archivo para replicarlo.
    """
    if 'file' not in request.files:
        return "No file part in request", 400
    file = request.files['file']
    # Se utiliza el nombre del archivo enviado en form-data o el nombre del archivo mismo
    filename = request.form.get('filename', file.filename)
    if filename == '':
        return "No filename provided", 400

    filepath = os.path.join(REPLICA_STORAGE, filename)
    file.save(filepath)
    return f"Archivo '{filename}' replicado exitosamente en la réplica.", 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Permite descargar un archivo desde la Réplica (opcional).
    """
    return send_from_directory(REPLICA_STORAGE, filename, as_attachment=True)

@app.route('/files', methods=['GET'])
def list_files():
    """
    Devuelve la lista de archivos almacenados en la Réplica (opcional).
    """
    files = os.listdir(REPLICA_STORAGE)
    return jsonify(files)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """
    Permite eliminar un archivo almacenado en la Réplica.
    """
    filepath = os.path.join(REPLICA_STORAGE, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return f"Archivo '{filename}' eliminado exitosamente en la réplica.", 200
        except Exception as e:
            return f"Error al eliminar el archivo '{filename}': {e}", 500
    else:
        return f"Archivo '{filename}' no encontrado en la réplica.", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
