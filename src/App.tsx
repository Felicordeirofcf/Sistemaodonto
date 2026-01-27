import React from 'react';
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

// --- NOVAS IMPORTAÇÕES PROFISSIONAIS ---
import { DashboardVendas } from './pages/DashboardVendas'; 
import { ConfigProcedimentos } from './pages/ConfigProcedimentos';
import { MarketingCampaigns } from './pages/MarketingCampaigns';

// Rota Privada Blindada
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('odonto_token');
  // Se não houver token, redireciona para login
  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Todas as rotas internas ficam sob o PrivateRoute */}
        <Route path="/*" element={
          <PrivateRoute>
            <div className="flex min-h-screen bg-white font-sans">
              <Sidebar />
              <main className="flex-1 ml-0 md:ml-64 transition-all duration-300 w-full overflow-x-hidden">
                <Routes>
                  {/* Dashboards */}
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard-vendas" element={<DashboardVendas />} />
                  
                  {/* Operacional Odonto */}
                  <Route path="/pacientes" element={<Pacientes />} />
                  <Route path="/agenda" element={<Agenda />} />
                  <Route path="/odontograma" element={<Odontograma />} />
                  <Route path="/harmonizacao" element={<Harmonizacao />} />
                  
                  {/* Gestão e Configuração */}
                  <Route path="/financeiro" element={<Financeiro />} />
                  <Route path="/estoque" element={<Estoque />} />
                  <Route path="/config-procedimentos" element={<ConfigProcedimentos />} />
                  
                  {/* Marketing e Chatbot */}
                  <Route path="/marketing" element={<MarketingCRM />} />
                  <Route path="/marketing/campanhas" element={<MarketingCampaigns />} />
                  <Route path="/atende-chat" element={<AtendeChat />} />

                  {/* Redirecionamento de segurança para rotas inexistentes */}
                  <Route path="*" element={<Navigate to="/" replace />} />
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