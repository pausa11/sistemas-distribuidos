import React, { useState, useEffect } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeFileList, setActiveFileList] = useState([]);

  // Definición de las URLs de los servidores
  const PRIMARY_SERVER_URL = "http://192.168.20.17:5000"; // Computador A (subida)
  const SECONDARY_SERVER_URL = "http://192.168.20.17:5001"; // Computador B (fallback para subida, listado, descarga y eliminación)
  const TERTIARY_SERVER_URL = "http://192.168.20.17:5002"; // Computador C (listado y eliminación)
  const FOURTH_SERVER_URL = "http://192.168.20.17:5003"; // Computador D (descarga)

  // Arreglos de servidores para cada operación según los roles:
  const uploadServers = [PRIMARY_SERVER_URL, SECONDARY_SERVER_URL];
  const listServers = [TERTIARY_SERVER_URL, SECONDARY_SERVER_URL];
  const downloadServers = [FOURTH_SERVER_URL, SECONDARY_SERVER_URL];
  const deleteServers = [TERTIARY_SERVER_URL, SECONDARY_SERVER_URL];

  // Manejo del cambio en el input de tipo file
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  // Función auxiliar con fallback: prueba cada servidor en el arreglo dado
  const tryRequestInOrder = async (endpoint, options = {}, servers) => {
    for (const url of servers) {
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

  // Subida: se intenta primero en Computador A, luego B
  const handleUpload = async () => {
    if (!selectedFile) {
      alert("No has seleccionado ningún archivo.");
      return;
    }
    const formData = new FormData();
    formData.append("file", selectedFile);
    try {
      const { response, serverUrl } = await tryRequestInOrder(
        "/upload",
        { method: "POST", body: formData },
        uploadServers
      );
      const result = await response.text();
      console.log(`Respuesta del servidor (${serverUrl}): ${result}`);
      fetchActiveFileList();
    } catch (error) {
      console.error("Error subiendo el archivo:", error);
    }
  };

  // Listado: se obtiene desde Computador C; si falla, se intenta con B
  const fetchActiveFileList = async () => {
    try {
      const { response, serverUrl } = await tryRequestInOrder(
        "/files",
        {},
        listServers
      );
      const data = await response.json();
      setActiveFileList(data);
      console.log(`Lista obtenida de ${serverUrl}`);
    } catch (error) {
      console.error("Error obteniendo la lista de archivos:", error);
    }
  };

  // Descarga: se descarga desde Computador D; si falla, se intenta con B
  const handleDownload = async (filename) => {
    try {
      const { response, serverUrl } = await tryRequestInOrder(
        `/download/${filename}`,
        {},
        downloadServers
      );
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      console.log(`Archivo descargado de ${serverUrl}`);
    } catch (error) {
      console.error("Error descargando el archivo:", error);
    }
  };

  // Eliminación: se elimina a través de Computador C; si falla, se recurre a B
  const handleDelete = async (filename) => {
    try {
      const { response, serverUrl } = await tryRequestInOrder(
        `/delete/${filename}`,
        { method: "DELETE" },
        deleteServers
      );
      const result = await response.text();
      console.log(`Archivo eliminado de ${serverUrl}: ${result}`);
      fetchActiveFileList();
    } catch (error) {
      console.error("Error eliminando el archivo:", error);
    }
  };

  useEffect(() => {
    fetchActiveFileList();
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Mini sistema distribuido de almacenamiento de archivos</h1>
      <div style={{ marginBottom: "1rem" }}>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} style={{ marginLeft: "8px" }}>
          Subir Archivo (Computador A)
        </button>
      </div>
      <h2>Archivos Activos (Listado desde C, fallback B)</h2>
      {activeFileList.length === 0 ? (
        <p>No hay archivos disponibles.</p>
      ) : (
        <ul>
          {activeFileList.map((file) => (
            <li key={file} style={{ margin: "8px 0" }}>
              {file}{" "}
              <button onClick={() => handleDownload(file)}>
                Descargar (D, fallback B)
              </button>
              <button onClick={() => handleDelete(file)} style={{ marginLeft: "8px" }}>
                Eliminar (C, fallback B)
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;
