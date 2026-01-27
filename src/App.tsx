import React, { useState, useEffect } from 'react';
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

// NOVAS IMPORTAÇÕES PROFISSIONAIS
import { DashboardVendas } from './pages/DashboardVendas'; 
import { ConfigProcedimentos } from './pages/ConfigProcedimentos';
import { MarketingCampaigns } from './pages/MarketingCampaigns';
import { GestaoEquipe } from './pages/GestaoEquipe';

// COMPONENTE DE BLOQUEIO (UI)
const BloqueioPagamento = () => (
  <div className="fixed inset-0 bg-slate-900/95 z-[9999] flex items-center justify-center p-4 backdrop-blur-sm">
    <div className="bg-white p-8 rounded-3xl max-w-md text-center shadow-2xl">
      <div className="w-20 h-20 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-10 h-10">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.248-8.25-3.286zm0 13.036h.008v.008H12v-.008z" />
        </svg>
      </div>
      <h2 className="text-2xl font-bold text-gray-800 mb-2">Acesso Suspenso</h2>
      <p className="text-gray-500 mb-8">Identificamos uma pendência financeira em sua assinatura. Regularize para liberar o acesso aos dados da clínica.</p>
      <button className="w-full py-4 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-200">
        Regularizar Agora
      </button>
    </div>
  </div>
);

// ROTA PRIVADA COM VERIFICAÇÃO DE STATUS
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('odonto_token');
  const [isActive, setIsActive] = useState<boolean | null>(null);

  useEffect(() => {
    if (token) {
      // Verifica o status da clínica no backend
      fetch('/api/auth/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => setIsActive(data.is_active))
      .catch(() => setIsActive(true)); // Fallback em caso de erro de rede
    }
  }, [token]);

  if (!token) return <Navigate to="/login" replace />;
  if (isActive === false) return <BloqueioPagamento />; // Exibe o bloqueio visual
  
  return <>{children}</>;
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
                  <Route path="/gestao-equipe" element={<GestaoEquipe />} />
                  
                  {/* Marketing e Chatbot */}
                  <Route path="/marketing" element={<MarketingCRM />} />
                  <Route path="/marketing/campanhas" element={<MarketingCampaigns />} />
                  <Route path="/atende-chat" element={<AtendeChat />} />

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