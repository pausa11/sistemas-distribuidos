import React, { useState, useEffect } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileList, setFileList] = useState([]);

  // Ajusta esta constante a la IP/puerto de tu servidor Primario
  const PRIMARY_SERVER_URL = "http://192.168.20.12:5000";

  // Maneja el cambio del input de tipo "file"
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  // Sube el archivo seleccionado al servidor Primario
  const handleUpload = async () => {
    if (!selectedFile) {
      alert("No has seleccionado ningún archivo.");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      // Petición POST al endpoint /upload
      const response = await fetch(`${PRIMARY_SERVER_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Error al subir archivo: ${response.statusText}`);
      }

      const result = await response.text();
      console.log("Respuesta del servidor:", result);

      // Actualizamos la lista de archivos después de subir uno nuevo
      fetchFileList();
    } catch (error) {
      console.error("Error subiendo archivo:", error);
    }
  };

  // Descarga de la lista de archivos existentes en el Primario
  const fetchFileList = async () => {
    try {
      const response = await fetch(`${PRIMARY_SERVER_URL}/files`);
      if (!response.ok) {
        throw new Error(`Error al obtener lista de archivos: ${response.statusText}`);
      }
      const data = await response.json(); // El servidor devuelve un JSON con un array de nombres de archivo
      setFileList(data);
    } catch (error) {
      console.error("Error al obtener lista de archivos:", error);
    }
  };

  // Función para descargar un archivo (abre en otra pestaña)
  const handleDownload = (filename) => {
    window.open(`${PRIMARY_SERVER_URL}/download/${filename}`, "_blank");
  };

  // Al montar el componente, obtenemos la lista de archivos
  useEffect(() => {
    fetchFileList();
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Sistema Distribuido</h1>

      <div style={{ marginBottom: "1rem" }}>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} style={{ marginLeft: "8px" }}>
          Subir Archivo
        </button>
      </div>

      <h2>Archivos en el Servidor Primario</h2>
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
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;
