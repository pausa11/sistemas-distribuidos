import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './components/Auth';         // Componente para login/registro
import FileManager from './components/FileManager'; // Componente para la interacción con archivos

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Auth />} />
        <Route path="/files" element={<FileManager />} />
        {/* Ruta por defecto redirige al login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </HashRouter>
  );
}

export default App;
