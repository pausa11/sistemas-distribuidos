import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

function Auth() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  // Suponemos que los endpoints de registro y login están en Computador A
  const SERVER_URL = "http://192.168.20.12:5000";

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
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h2>{isRegister ? "Register" : "Login"}</h2>
      <div style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ marginRight: "8px" }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      <div>
        <button onClick={isRegister ? handleRegister : handleLogin}>
          {isRegister ? "Register" : "Login"}
        </button>
        <button
          onClick={() => {
            setIsRegister(!isRegister);
            setMessage("");
          }}
          style={{ marginLeft: "8px" }}
        >
          {isRegister ? "Go to Login" : "Go to Register"}
        </button>
      </div>
      {message && <p>{message}</p>}
    </div>
  );
}

export default Auth;
