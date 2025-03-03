import React, { useState, useEffect } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileList, setFileList] = useState([]);

  // Direcciones de los 3 servidores
  const PRIMARY_SERVER_URL = "https://maquinaa.onrender.com";
  const SECONDARY_SERVER_URL = "https://maquina-b.onrender.com";
  const TERTIARY_SERVER_URL = "http://192.168.20.12:5002";

  // Agrupamos los servidores en un array para recorrerlos en orden
  const serverUrls = [PRIMARY_SERVER_URL, SECONDARY_SERVER_URL, TERTIARY_SERVER_URL];

  // Maneja el cambio del input de tipo "file"
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  // Función auxiliar que intenta hacer una petición a cada servidor en orden hasta que una responda correctamente
  const tryRequestInOrder = async (endpoint, options = {}) => {
    for (const url of serverUrls) {
      try {
        const response = await fetch(`${url}${endpoint}`, options);
        if (response.ok) {
          return { response, serverUrl: url };
        } else {
          console.error(`Error de ${url}${endpoint}: ${response.statusText}`);
        }
      } catch (error) {
        console.error(`Fallo al conectar a ${url}${endpoint}:`, error);
      }
    }
    throw new Error(`Ningún servidor respondió para el endpoint: ${endpoint}`);
  };

  // Sube el archivo seleccionado con fallback
  const handleUpload = async () => {
    if (!selectedFile) {
      alert("No has seleccionado ningún archivo.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const { response, serverUrl } = await tryRequestInOrder("/upload", {
        method: "POST",
        body: formData,
      });
      const result = await response.text();
      console.log(`Respuesta del servidor (${serverUrl}):`, result);
      // Actualizamos la lista de archivos después de subir uno nuevo
      fetchFileList();
    } catch (error) {
      console.error("Error subiendo el archivo en todos los servidores:", error);
    }
  };

  // Obtiene la lista de archivos con fallback
  const fetchFileList = async () => {
    try {
      const { response, serverUrl } = await tryRequestInOrder("/files");
      const data = await response.json();
      setFileList(data);
      console.log(`Lista de archivos obtenida de ${serverUrl}`);
    } catch (error) {
      console.error("Error al obtener lista de archivos en todos los servidores:", error);
    }
  };

  // Descarga un archivo con fallback (usando fetch y creando un enlace temporal)
  const handleDownload = async (filename) => {
    try {
      const { response, serverUrl } = await tryRequestInOrder(`/download/${filename}`);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      console.log(`Archivo descargado desde ${serverUrl}`);
    } catch (error) {
      console.error("Error al descargar el archivo en todos los servidores:", error);
    }
  };

  // Elimina un archivo con fallback
  const handleDelete = async (filename) => {
    try {
      const { response, serverUrl } = await tryRequestInOrder(`/delete/${filename}`, {
        method: "DELETE",
      });
      const result = await response.text();
      console.log(`Archivo eliminado desde ${serverUrl}: ${result}`);
      // Actualizamos la lista de archivos después de eliminar
      fetchFileList();
    } catch (error) {
      console.error("Error al eliminar el archivo en todos los servidores:", error);
    }
  };

  // Al montar el componente, obtenemos la lista de archivos
  useEffect(() => {
    fetchFileList();
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Mini sistema distribuido de almacenamiento de archivos</h1>

      <div style={{ marginBottom: "1rem" }}>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} style={{ marginLeft: "8px" }}>
          Subir Archivo
        </button>
      </div>

      <h2>Archivos (fallback automático)</h2>
      {fileList.length === 0 ? (
        <p>No hay archivos disponibles.</p>
      ) : (
        <ul>
          {fileList.map((file) => (
            <li key={file} style={{ margin: "8px 0" }}>
              {file}{" "}
              <button onClick={() => handleDownload(file)}>
                Descargar
              </button>
              <button onClick={() => handleDelete(file)} style={{ marginLeft: "8px" }}>
                Eliminar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;
