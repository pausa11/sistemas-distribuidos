import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Auth() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  // Endpoints: Computador A y réplica
  const SERVER_URL = "https://maquinaa.onrender.com";
  const REPLICATION_URL = "https://sistemas-distribuidos-1.onrender.com";

  // Función auxiliar para intentar una petición en ambos servidores
  const tryRequest = async (path, options) => {
    // Primero intenta en Computador A
    try {
      let response = await fetch(`${SERVER_URL}${path}`, options);
      // Si la respuesta no es ok y el error es del servidor, se intenta el replica
      if (!response.ok && response.status >= 500) {
        throw new Error("Primary server error");
      }
      return response;
    } catch (error) {
      // Intenta en el servidor de réplica
      try {
        let response = await fetch(`${REPLICATION_URL}${path}`, options);
        return response;
      } catch (error2) {
        throw new Error("Error on both servers: " + error2.message);
      }
    }
  };

  // Función para registrar un usuario
  const handleRegister = async () => {
    const options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    };

    try {
      const response = await tryRequest("/register", options);
      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        setIsRegister(false); // Cambia a modo login
      } else {
        setMessage(data.error || "Registration failed");
      }
    } catch (error) {
      setMessage("Error: " + error.message);
    }
  };

  // Función para loguear un usuario
  const handleLogin = async () => {
    const options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    };

    try {
      const response = await tryRequest("/login", options);
      const data = await response.json();
      if (response.ok) {
        setMessage(data.message);
        // Redirigir a la ruta del File Manager pasando el user_id en el state
        navigate("/files", { state: { userId: data.user_id } });
      } else {
        setMessage(data.error || "Login failed");
      }
    } catch (error) {
      setMessage("Error: " + error.message);
    }
  };

  return (
    <div className="p-8 font-sans">
      <h2 className="text-2xl font-bold mb-4">
        {isRegister ? "Register" : "Login"}
      </h2>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mr-2 p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="p-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
        />
      </div>
      <div>
        <button
          onClick={isRegister ? handleRegister : handleLogin}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          {isRegister ? "Register" : "Login"}
        </button>
        <button
          onClick={() => {
            setIsRegister(!isRegister);
            setMessage("");
          }}
          className="ml-2 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
        >
          {isRegister ? "Go to Login" : "Go to Register"}
        </button>
      </div>
      {message && <p className="mt-4 text-red-500">{message}</p>}
    </div>
  );
}

export default Auth;
