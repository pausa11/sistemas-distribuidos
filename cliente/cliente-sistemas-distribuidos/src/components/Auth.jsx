import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Auth() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  // Suponemos que los endpoints de registro y login están en Computador A
  const SERVER_URL = "https://maquinaa.onrender.com";

  // Función para registrar un usuario
  const handleRegister = async () => {
    try {
      const response = await fetch(`${SERVER_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
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
    try {
      const response = await fetch(`${SERVER_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
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
