import React, { useState, useEffect } from 'react';

// --- TIPAGEM ---
interface AutomationRule {
  id: number;
  nome: string;
  dias_ausente: number;
  horario: string;
  mensagem: string;
  ativo: boolean;
}

const MarketingPage: React.FC = () => {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Estado do Formulário
  const [formData, setFormData] = useState({
    nome: '',
    dias_ausente: 180,
    horario: '09:00',
    mensagem: 'Olá {nome}, faz tempo que não te vemos! Vamos cuidar desse sorriso? 🦷'
  });

  // ✅ CORREÇÃO APLICADA: URL Relativa
  // Ao usar apenas "/api/marketing", funciona tanto localmente quanto no Render (HTTPS).
  const API_URL = '/api/marketing'; 
  
  // Pega o token salvo no login (mesma chave usada no App.tsx)
  const token = localStorage.getItem('odonto_token'); 

  // --- BUSCAR REGRAS (GET) ---
  const fetchRules = async () => {
    try {
      const res = await fetch(`${API_URL}/automations`, {
        method: 'GET',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!res.ok) throw new Error('Erro ao buscar regras');
      
      const data = await res.json();
      setRules(data);
    } catch (error) {
      console.error("Erro ao buscar regras:", error);
    } finally {
      setLoading(false);
    }
  };

  // Carrega as regras ao abrir a página
  useEffect(() => {
    fetchRules();
  }, []);

  // --- SALVAR NOVA REGRA (POST) ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/automations`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!res.ok) throw new Error('Erro ao salvar');

      setIsModalOpen(false); // Fecha o modal
      fetchRules(); // Atualiza a lista na tela
      
      // Limpa o formulário (opcional)
      setFormData({
        nome: '',
        dias_ausente: 180,
        horario: '09:00',
        mensagem: 'Olá {nome}, faz tempo que não te vemos! Vamos cuidar desse sorriso? 🦷'
      });

    } catch (error) {
      alert('Erro ao salvar regra. Verifique se está logado.');
    }
  };

  // --- DELETAR REGRA (DELETE) ---
  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja apagar este robô?')) return;
    try {
      const res = await fetch(`${API_URL}/automations/${id}`, {
        method: 'DELETE',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!res.ok) throw new Error('Erro ao deletar');
      
      fetchRules(); // Atualiza a lista
    } catch (error) {
      alert('Erro ao deletar regra.');
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen text-gray-800">
      
      {/* CABEÇALHO */}
      <div className="flex justify-between items-center mb-8">
        <div>
            <h1 className="text-3xl font-bold text-slate-800">🤖 Automação de Recall</h1>
            <p className="text-gray-500">Configure robôs para trazer seus pacientes de volta automaticamente.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg shadow flex items-center gap-2 transition"
        >
          <span className="text-xl font-bold">+</span> Nova Regra
        </button>
      </div>

      {/* CARD STATUS DO ROBÔ */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white shadow-lg mb-8 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold">O Robô está Ativo</h2>
          <p className="opacity-90 mt-1">O sistema verifica pacientes sumidos a cada 1 hora e envia mensagens automaticamente.</p>
        </div>
        <div className="text-5xl opacity-30">⚙️</div>
      </div>

      {/* LISTA DE REGRAS */}
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <h3 className="text-lg font-bold mb-4 border-b pb-2 text-gray-700">Regras Configuradas</h3>
        
        {loading ? (
          <div className="text-center py-4 text-gray-500">Carregando regras...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rules.length === 0 && (
                <div className="col-span-3 text-center py-8 text-gray-400 border-2 border-dashed rounded-lg">
                    <p>Nenhuma regra ativa.</p>
                    <p className="text-sm">Clique em "Nova Regra" para começar.</p>
                </div>
            )}
            
            {rules.map((rule) => (
              <div key={rule.id} className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition bg-white relative group">
                <button 
                  onClick={() => handleDelete(rule.id)}
                  className="absolute top-4 right-4 text-gray-300 hover:text-red-500 transition"
                  title="Excluir Regra"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                </button>
                
                <h4 className="font-bold text-lg text-blue-600 mb-2">{rule.nome}</h4>
                
                <div className="text-sm text-gray-600 space-y-1 mb-4">
                  <p className="flex items-center gap-2">
                    🕒 Dispara às <strong>{rule.horario}</strong>
                  </p>
                  <p className="flex items-center gap-2">
                    📅 Ausência de <strong>{rule.dias_ausente} dias</strong>
                  </p>
                </div>
                
                <div className="bg-green-50 p-3 rounded text-xs text-green-800 border border-green-100 italic relative">
                  <span className="absolute -top-2 left-2 bg-white px-1 text-[10px] text-green-600 font-bold border rounded">WhatsApp</span>
                  "{rule.mensagem}"
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* PRÉVIA DO KANBAN (Visual Apenas - Conectaremos ao Banco em breve) */}
      <h3 className="text-2xl font-bold text-slate-800 mb-4">Funil de Recuperação (CRM)</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* COLUNA 1: A CONTACTAR */}
        <div className="bg-gray-100 p-4 rounded-xl min-h-[200px]">
          <div className="font-bold text-gray-500 mb-4 flex justify-between items-center">
            <span>A CONTACTAR</span>
            <span className="bg-gray-300 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">Auto</span>
          </div>
          {/* Card Exemplo */}
          <div className="bg-white p-4 rounded-lg shadow-sm mb-3 border-l-4 border-yellow-400 cursor-pointer hover:shadow-md transition">
            <div className="font-bold text-gray-800">Maria Silva</div>
            <div className="text-xs text-gray-500 mt-1">Robô enviou msg hoje às 09:00</div>
          </div>
        </div>

         {/* COLUNA 2: RESPONDIDOS */}
         <div className="bg-gray-100 p-4 rounded-xl min-h-[200px]">
          <div className="font-bold text-blue-600 mb-4">RESPONDIDOS</div>
          {/* Card Exemplo */}
          <div className="bg-white p-4 rounded-lg shadow-sm mb-3 border-l-4 border-blue-500 cursor-pointer hover:shadow-md transition">
            <div className="font-bold text-gray-800">João Souza</div>
            <div className="text-xs text-gray-500 mt-1">💬 "Vou ver minha agenda..."</div>
          </div>
        </div>

         {/* COLUNA 3: RECUPERADOS */}
         <div className="bg-gray-100 p-4 rounded-xl min-h-[200px]">
          <div className="font-bold text-green-600 mb-4">RECUPERADOS</div>
          {/* Card Exemplo */}
          <div className="bg-white p-4 rounded-lg shadow-sm mb-3 border-l-4 border-green-500 cursor-pointer hover:shadow-md transition opacity-75">
            <div className="font-bold text-gray-800">Ana Clara</div>
            <div className="text-xs text-gray-500 mt-1">✅ Agendou para 15/02</div>
          </div>
        </div>

      </div>

      {/* MODAL DE CRIAÇÃO */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 transform transition-all scale-100">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Criar Nova Automação</h2>
            
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2 text-gray-700">Nome da Regra</label>
                <input 
                  type="text" 
                  className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition" 
                  value={formData.nome}
                  onChange={e => setFormData({...formData, nome: e.target.value})}
                  placeholder="Ex: Recall 6 Meses" 
                  required 
                />
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-bold mb-2 text-gray-700">Dias Ausente</label>
                  <input 
                    type="number" 
                    className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition" 
                    value={formData.dias_ausente}
                    onChange={e => setFormData({...formData, dias_ausente: Number(e.target.value)})}
                    required 
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold mb-2 text-gray-700">Horário</label>
                  <input 
                    type="time" 
                    className="w-full border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition" 
                    value={formData.horario}
                    onChange={e => setFormData({...formData, horario: e.target.value})}
                    required 
                  />
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-bold mb-2 text-gray-700">Mensagem do WhatsApp</label>
                <textarea 
                  className="w-full border border-gray-300 p-3 rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none transition" 
                  rows={4}
                  value={formData.mensagem}
                  onChange={e => setFormData({...formData, mensagem: e.target.value})}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Use <strong>{'{nome}'}</strong> para inserir o nome do paciente.</p>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="px-5 py-2.5 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition"
                >
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-lg shadow-blue-500/30 transition"
                >
                  Salvar Robô
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default MarketingPage;