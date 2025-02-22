import os
import requests
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# Carpeta donde guardamos los archivos descargados del Primario como backup
BACKUP_STORAGE = "./data_backup"
os.makedirs(BACKUP_STORAGE, exist_ok=True)

# Sustituir por la IP o hostname y puerto del Server 1 (Primario)
PRIMARY_URL = "http://192.168.20.12:5000"

def do_backup():
    """
    Llama a /files en el Primario para conocer la lista de archivos
    y descarga aquellos que no tengamos aún en nuestro backup local.
    """
    try:
        resp = requests.get(f"{PRIMARY_URL}/files")
        if resp.status_code != 200:
            print("Error al obtener la lista de archivos del Primario.")
            return

        files = resp.json()  # Se espera una lista con los nombres de archivo

        for filename in files:
            local_path = os.path.join(BACKUP_STORAGE, filename)
            # Si no existe localmente, lo descargamos
            if not os.path.exists(local_path):
                download_url = f"{PRIMARY_URL}/download/{filename}"
                file_resp = requests.get(download_url, stream=True)
                if file_resp.status_code == 200:
                    with open(local_path, 'wb') as f:
                        for chunk in file_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Backed up file: {filename}")
                else:
                    print(f"Error al descargar {filename} desde el Primario.")
    except Exception as e:
        print(f"Exception during backup: {e}")

@app.route('/backup', methods=['GET'])
def backup_route():
    """
    Endpoint para iniciar la operación de backup de forma manual.
    """
    do_backup()
    return "Respaldo (backup) completado.", 200

@app.route('/files', methods=['GET'])
def list_backup_files():
    """
    Lista de archivos que ya tenemos en nuestro almacenamiento de respaldo.
    """
    files = os.listdir(BACKUP_STORAGE)
    return jsonify(files)

@app.route('/download/<filename>', methods=['GET'])
def download_backup_file(filename):
    """
    Permite descargar desde este servidor de respaldo alguno de los archivos
    que ya haya copiado.
    """
    return send_from_directory(BACKUP_STORAGE, filename, as_attachment=True)

if __name__ == "__main__":
    # Escucha en el puerto 5002
    app.run(host='0.0.0.0', port=5002)
