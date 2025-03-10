import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";

function FileManager() {
  const location = useLocation();
  const { userId } = location.state || {}; // Se espera que se haya pasado el userId al navegar
  
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeFileList, setActiveFileList] = useState([]);

  // Definición de las URLs de los servidores
  const PRIMARY_SERVER_URL = "https://maquinaa.onrender.com"; // Computador A (subida)
  const SECONDARY_SERVER_URL = "https://maquina-b.onrender.com"; // Computador B (fallback para subida, listado, descarga y eliminación)
  const TERTIARY_SERVER_URL = "https://maquinac.onrender.com"; // Computador C (listado y eliminación)
  const FOURTH_SERVER_URL = "https://sistemas-distribuidos-scrq.onrender.com"; // Computador D (descarga)
  const FIFTH_SERVER_URL = "https://sistemas-distribuidos-1.onrender.com"; // Computador E (fallback para subida)

  // Arreglos de servidores para cada operación según los roles:
  // Se añadió el FIFTH_SERVER_URL al arreglo de subida para tener un fallback adicional
  const uploadServers = [PRIMARY_SERVER_URL, SECONDARY_SERVER_URL, FIFTH_SERVER_URL];
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

  // Subida: se intenta primero en Computador A, luego en B y finalmente en E.
  // Se envía el user_id.
  const handleUpload = async () => {
    if (!selectedFile) {
      alert("No has seleccionado ningún archivo.");
      return;
    }
    if (!userId) {
      alert("No se ha proporcionado userId.");
      return;
    }
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("user_id", userId);
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

  // Listado: se obtiene desde Computador C; si falla, se intenta con B.
  // Se pasa user_id como query string.
  const fetchActiveFileList = async () => {
    if (!userId) {
      console.error("userId no proporcionado");
      return;
    }
    try {
      const { response, serverUrl } = await tryRequestInOrder(
        `/files?user_id=${userId}`,
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

  // Descarga: se descarga desde Computador D; si falla, se intenta con B.
  // Se pasa user_id opcionalmente para confirmar que el usuario tiene acceso.
  const handleDownload = async (filename) => {
    try {
      const { response, serverUrl } = await tryRequestInOrder(
        `/download/${filename}?user_id=${userId}`,
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

  // Eliminación: se elimina a través de Computador C; si falla, se recurre a B.
  // Se pasa user_id para verificar la propiedad del archivo.
  const handleDelete = async (filename) => {
    try {
      const { response, serverUrl } = await tryRequestInOrder(
        `/delete/${filename}?user_id=${userId}`,
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
    if (userId) {
      fetchActiveFileList();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  return (
    <div className="p-8 font-sans">
      <h1 className="text-3xl font-bold mb-4">File Manager</h1>
      <div className="mb-4">
        <input 
          type="file" 
          onChange={handleFileChange} 
          className="border border-gray-300 p-2 rounded"
        />
        <button 
          onClick={handleUpload} 
          className="ml-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Upload File
        </button>
      </div>
      <h2 className="text-2xl font-semibold mb-2">Active Files</h2>
      {activeFileList.length === 0 ? (
        <p>No files available.</p>
      ) : (
        <ul>
          {activeFileList.map((file) => (
            <li key={file} className="mb-2">
              {file} 
              <button 
                onClick={() => handleDownload(file)}
                className="ml-2 px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
              >
                Download
              </button>
              <button 
                onClick={() => handleDelete(file)}
                className="ml-2 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default FileManager;
