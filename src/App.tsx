import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { MarketingCRM } from './pages/MarketingCRM';
import { Dashboard } from './pages/Dashboard';
import { AtendeChat } from './pages/AtendeChat';
import { Odontograma } from './pages/Odontograma';
import { Financeiro } from './pages/Financeiro';
import { Agenda } from './pages/Agenda';
import { Harmonizacao } from './pages/Harmonizacao';

// Componente Placeholder simples para páginas em construção
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="p-8">
    <h1 className="text-3xl font-bold text-gray-800 mb-4">{title}</h1>
    <div className="p-10 bg-white rounded-lg border border-dashed border-gray-300 text-center text-gray-500">
      Módulo em desenvolvimento...
    </div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-background font-sans">
        <Sidebar />
        {/* AQUI ESTÁ O TRUQUE: 'ml-0' no mobile, 'md:ml-64' no desktop */}
        <main className="flex-1 ml-0 md:ml-64 transition-all duration-300 w-full">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/atende-chat" element={<AtendeChat />} />
            <Route path="/odontograma" element={<Odontograma />} />
            <Route path="/marketing" element={<MarketingCRM />} />
            <Route path="/harmonizacao" element={<Harmonizacao />} />
            
            <Route path="/agenda" element={<Agenda />} />
            <Route path="/pacientes" element={<PlaceholderPage title="Gestão de Pacientes" />} />
            <Route path="/financeiro" element={<Financeiro />} />
            <Route path="/estoque" element={<PlaceholderPage title="Controle de Estoque" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;