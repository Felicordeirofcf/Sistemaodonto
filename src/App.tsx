import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { MarketingCRM } from './pages/MarketingCRM';
import { Dashboard } from './pages/Dashboard';

// Componente simples para páginas que ainda não criamos
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="p-10">
    <h1 className="text-3xl font-bold text-primary mb-4">{title}</h1>
    <div className="bg-white p-12 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center">
      <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mb-4">
        <span className="text-2xl">🚧</span>
      </div>
      <h2 className="text-xl font-semibold text-gray-800">Em Desenvolvimento</h2>
      <p className="text-gray-500 max-w-md mt-2">
        Este módulo estará disponível em breve. Por enquanto, explore o módulo de 
        <span className="text-primary font-bold"> Marketing & CRM</span>.
      </p>
    </div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-background font-sans">
        {/* Sidebar Fixa */}
        <Sidebar />
        
        {/* Conteúdo Principal (com margem para não ficar baixo da sidebar) */}
        <main className="flex-1 ml-64 transition-all duration-300">
          <Routes>
            {/* Redireciona a home para o Marketing por enquanto, pois é o que está pronto */}
            <Route path="/" element={<Dashboard />} />
            
            <Route path="/marketing" element={<MarketingCRM />} />
            
            <Route path="/agenda" element={<PlaceholderPage title="Agenda Inteligente" />} />
            <Route path="/pacientes" element={<PlaceholderPage title="Gestão de Pacientes" />} />
            <Route path="/financeiro" element={<PlaceholderPage title="Controle Financeiro" />} />
            <Route path="/estoque" element={<PlaceholderPage title="Controle de Estoque" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;