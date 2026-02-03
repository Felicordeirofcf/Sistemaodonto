import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Loader2, ShieldAlert } from 'lucide-react';

// --- IMPORTAÇÕES DE PÁGINAS ---
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Pacientes } from './pages/Pacientes';
import { Agenda } from './pages/Agenda';
import { Harmonizacao } from './pages/Harmonizacao';
import { Financeiro } from './pages/Financeiro';
import { Estoque } from './pages/Estoque';
import { GestaoEquipe } from './pages/GestaoEquipe';
import { Configuracoes } from './pages/Configuracoes';
import { LandingPage } from './pages/LandingPage';
import { WhatsAppModulePage } from './pages/WhatsAppModulePage';
import MarketingPage from './pages/MarketingPage';

const BloqueioPagamento = () => (
  <div className="fixed inset-0 bg-slate-900/95 z-[9999] flex items-center justify-center p-4 backdrop-blur-sm">
    <div className="bg-white p-10 rounded-[3rem] max-w-md text-center shadow-2xl border border-red-50 animate-in zoom-in duration-300">
      <div className="w-24 h-24 bg-red-100 text-red-600 rounded-[2rem] flex items-center justify-center mx-auto mb-8 shadow-lg shadow-red-100">
        <ShieldAlert size={48} strokeWidth={2.5} />
      </div>
      <h2 className="text-3xl font-black text-gray-900 mb-2 tracking-tight">Acesso Suspenso</h2>
      <p className="text-gray-500 mb-10 font-medium leading-relaxed">Regularize sua assinatura para liberar o acesso total aos dados da sua clínica.</p>
      <button className="w-full py-5 bg-blue-600 text-white rounded-[1.5rem] font-black text-xs uppercase tracking-[0.2em] hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 active:scale-95">
        Regularizar Agora
      </button>
    </div>
  </div>
);

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('odonto_token');
  const [isActive, setIsActive] = useState<boolean | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (token) {
      fetch('/auth/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => {
        if (!res.ok) throw new Error("Erro de Autenticação");
        return res.json();
      })
      .then(data => setIsActive(data.is_active))
      .catch(() => setIsActive(true))
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
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/api/*" element={null} />
        <Route path="/auth/*" element={null} />
        
        <Route path="/app/*" element={
          <PrivateRoute>
            <div className="flex min-h-screen bg-gray-50 font-sans">
              <Sidebar />
              <main className="flex-1 md:ml-64 transition-all duration-300 w-full overflow-x-hidden">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/pacientes" element={<Pacientes />} />
                  <Route path="/agenda" element={<Agenda />} />
                  <Route path="/harmonizacao" element={<Harmonizacao />} />
                  <Route path="/financeiro" element={<Financeiro />} />
                  <Route path="/estoque" element={<Estoque />} />
                  <Route path="/gestao-equipe" element={<GestaoEquipe />} />
                  <Route path="/whatsapp" element={<WhatsAppModulePage />} />
                  <Route path="/marketing" element={<MarketingPage />} />
                  <Route path="/configuracoes" element={<Configuracoes />} />
                  <Route path="*" element={<Navigate to="/app" replace />} />
                </Routes>
              </main>
            </div>
          </PrivateRoute>
        } />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
