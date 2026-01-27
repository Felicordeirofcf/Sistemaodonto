import React from 'react'; // <--- OBRIGATÓRIO
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { MarketingCRM } from './pages/MarketingCRM';
import { Dashboard } from './pages/Dashboard';
import { AtendeChat } from './pages/AtendeChat';
import { Odontograma } from './pages/Odontograma';
import { Financeiro } from './pages/Financeiro';
import { Agenda } from './pages/Agenda';
import { Harmonizacao } from './pages/Harmonizacao';
import { Estoque } from './pages/Estoque';
import { Pacientes } from './pages/Pacientes';
import { Login } from './pages/Login';

// Definindo explicitamente o tipo dos children para evitar erro TS
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('odonto_token');
  return token ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={
          <PrivateRoute>
            <div className="flex min-h-screen bg-white font-sans">
              <Sidebar />
              <main className="flex-1 ml-0 md:ml-64 transition-all duration-300 w-full overflow-x-hidden">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/pacientes" element={<Pacientes />} />
                  <Route path="/agenda" element={<Agenda />} />
                  <Route path="/odontograma" element={<Odontograma />} />
                  <Route path="/harmonizacao" element={<Harmonizacao />} />
                  <Route path="/financeiro" element={<Financeiro />} />
                  <Route path="/estoque" element={<Estoque />} />
                  <Route path="/marketing" element={<MarketingCRM />} />
                  <Route path="/atende-chat" element={<AtendeChat />} />
                </Routes>
              </main>
            </div>
          </PrivateRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;