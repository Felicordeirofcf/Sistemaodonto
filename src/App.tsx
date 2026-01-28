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

// IMPORTAÇÕES PROFISSIONAIS E LANDING PAGE
import { LandingPage } from './pages/LandingPage';
import { DashboardVendas } from './pages/DashboardVendas'; 
import { ConfigProcedimentos } from './pages/ConfigProcedimentos';
import { MarketingCampaigns } from './pages/MarketingCampaigns';
import { GestaoEquipe } from './pages/GestaoEquipe';
import { Configuracoes } from './pages/Configuracoes';
import { Loader2 } from 'lucide-react'; // Para o estado de loading

// COMPONENTE DE BLOQUEIO (UI INDUSTRIAL)
const BloqueioPagamento = () => (
  <div className="fixed inset-0 bg-slate-900/95 z-[9999] flex items-center justify-center p-4 backdrop-blur-sm">
    <div className="bg-white p-10 rounded-[3rem] max-w-md text-center shadow-2xl border border-red-50 animate-in zoom-in duration-300">
      <div className="w-24 h-24 bg-red-100 text-red-600 rounded-[2rem] flex items-center justify-center mx-auto mb-8 shadow-lg shadow-red-100">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-12 h-12">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.248-8.25-3.286zm0 13.036h.008v.008H12v-.008z" />
        </svg>
      </div>
      <h2 className="text-3xl font-black text-gray-900 mb-2 tracking-tight">Acesso Suspenso</h2>
      <p className="text-gray-500 mb-10 font-medium leading-relaxed">Regularize sua assinatura para liberar o acesso total aos dados da sua clínica.</p>
      <button className="w-full py-5 bg-blue-600 text-white rounded-[1.5rem] font-black text-xs uppercase tracking-[0.2em] hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 active:scale-95">
        Regularizar Agora
      </button>
    </div>
  </div>
);

// ROTA PRIVADA COM VERIFICAÇÃO DE STATUS
const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('odonto_token');
  const [isActive, setIsActive] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (token) {
      // Bate no endpoint revisado no backend
      fetch('/auth/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then(data => setIsActive(data.is_active))
      .catch(() => setIsActive(true)) // Fallback em caso de erro de rede
      .finally(() => setChecking(false));
    } else {
      setChecking(false);
    }
  }, [token]);

  if (checking) return (
    <div className="h-screen w-full flex items-center justify-center bg-gray-50">
      <Loader2 className="animate-spin text-blue-600" size={48} />
    </div>
  );

  if (!token) return <Navigate to="/login" replace />;
  if (isActive === false) return <BloqueioPagamento />;
  
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rotas Públicas */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />

        {/* Rotas Protegidas do Sistema */}
        <Route path="/app/*" element={
          <PrivateRoute>
            <div className="flex min-h-screen bg-gray-50 font-sans">
              <Sidebar />
              {/* ml-64 fixo para desktop mantendo a sidebar visível */}
              <main className="flex-1 md:ml-64 transition-all duration-300 w-full overflow-x-hidden">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard-vendas" element={<DashboardVendas />} />
                  <Route path="/pacientes" element={<Pacientes />} />
                  <Route path="/agenda" element={<Agenda />} />
                  <Route path="/odontograma" element={<Odontograma />} />
                  <Route path="/harmonizacao" element={<Harmonizacao />} />
                  <Route path="/financeiro" element={<Financeiro />} />
                  <Route path="/estoque" element={<Estoque />} />
                  {/* Nome da rota unificado com o Sidebar */}
                  <Route path="/fichas-tecnicas" element={<ConfigProcedimentos />} />
                  <Route path="/gestao-equipe" element={<GestaoEquipe />} />
                  <Route path="/marketing" element={<MarketingCRM />} />
                  <Route path="/marketing/campanhas" element={<MarketingCampaigns />} />
                  <Route path="/atende-chat" element={<AtendeChat />} />
                  <Route path="/configuracoes" element={<Configuracoes />} />
                  
                  {/* Fallback interno: redireciona para o dashboard se a subrota não existir */}
                  <Route path="*" element={<Navigate to="/app" replace />} />
                </Routes>
              </main>
            </div>
          </PrivateRoute>
        } />

        {/* Fallback Global: Redireciona para Landing Page se não autenticado */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;