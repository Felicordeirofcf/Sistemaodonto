import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Certifique-se de ter axios instalado

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

  // URL da API (Ajuste conforme sua configuração)
  const API_URL = 'http://localhost:5000/api/marketing'; 
  const token = localStorage.getItem('token'); // Ajuste conforme você salva o token

  // --- BUSCAR REGRAS ---
  const fetchRules = async () => {
    try {
      const res = await axios.get(`${API_URL}/automations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRules(res.data);
    } catch (error) {
      console.error("Erro ao buscar regras", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  // --- SALVAR REGRA ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/automations`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsModalOpen(false);
      fetchRules(); // Recarrega a lista
    } catch (error) {
      alert('Erro ao salvar regra');
    }
  };

  // --- DELETAR REGRA ---
  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja apagar este robô?')) return;
    try {
      await axios.delete(`${API_URL}/automations/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchRules();
    } catch (error) {
      alert('Erro ao deletar');
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen text-gray-800">
      
      {/* CABEÇALHO */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-slate-800">🤖 Automação de Recall</h1>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-lg shadow flex items-center gap-2 transition"
        >
          <span>+</span> Nova Regra
        </button>
      </div>

      {/* CARD STATUS DO ROBÔ */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white shadow-lg mb-8 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold">O Robô está Ativo</h2>
          <p className="opacity-90 mt-1">Verificando pacientes sumidos a cada 1 hora.</p>
        </div>
        <div className="text-4xl opacity-50">🤖</div>
      </div>

      {/* LISTA DE REGRAS */}
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <h3 className="text-lg font-bold mb-4 border-b pb-2">Regras Configuradas</h3>
        
        {loading ? (
          <p>Carregando...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rules.length === 0 && <p className="text-gray-400">Nenhuma regra ativa.</p>}
            
            {rules.map((rule) => (
              <div key={rule.id} className="border rounded-lg p-4 hover:shadow-md transition bg-white relative">
                <button 
                  onClick={() => handleDelete(rule.id)}
                  className="absolute top-4 right-4 text-red-400 hover:text-red-600"
                >
                  🗑️
                </button>
                <h4 className="font-bold text-lg text-blue-600 mb-1">{rule.nome}</h4>
                <div className="text-sm text-gray-600 mb-3">
                  <p>🕒 Dispara às <strong>{rule.horario}</strong></p>
                  <p>📅 Ausência de <strong>{rule.dias_ausente} dias</strong></p>
                </div>
                <div className="bg-green-50 p-2 rounded text-xs text-green-800 border border-green-100 italic">
                  "{rule.mensagem}"
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* PRÉVIA DO KANBAN (Visual Apenas) */}
      <h3 className="text-2xl font-bold text-slate-800 mb-4">Funil de Recuperação (CRM)</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* COLUNA 1 */}
        <div className="bg-gray-100 p-4 rounded-xl">
          <div className="font-bold text-gray-500 mb-4 flex justify-between">
            A CONTACTAR <span className="bg-gray-300 px-2 rounded-full text-xs py-1">Auto</span>
          </div>
          <div className="bg-white p-3 rounded shadow mb-2 border-l-4 border-yellow-400">
            <div className="font-bold">Maria Silva</div>
            <div className="text-xs text-gray-500">Robô enviou msg hoje</div>
          </div>
        </div>
         {/* COLUNA 2 */}
         <div className="bg-gray-100 p-4 rounded-xl">
          <div className="font-bold text-blue-500 mb-4">RESPONDIDOS</div>
          <div className="bg-white p-3 rounded shadow mb-2 border-l-4 border-blue-400">
            <div className="font-bold">João Souza</div>
            <div className="text-xs text-gray-500">"Vou ver minha agenda"</div>
          </div>
        </div>
         {/* COLUNA 3 */}
         <div className="bg-gray-100 p-4 rounded-xl">
          <div className="font-bold text-green-600 mb-4">RECUPERADOS</div>
          <div className="bg-white p-3 rounded shadow mb-2 border-l-4 border-green-400">
            <div className="font-bold">Ana Clara</div>
            <div className="text-xs text-gray-500">Agendou para 15/02</div>
          </div>
        </div>
      </div>

      {/* MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6">
            <h2 className="text-2xl font-bold mb-4">Criar Automação</h2>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Nome da Regra</label>
                <input 
                  type="text" 
                  className="w-full border p-2 rounded" 
                  value={formData.nome}
                  onChange={e => setFormData({...formData, nome: e.target.value})}
                  placeholder="Ex: Recall 6 Meses" 
                  required 
                />
              </div>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-bold mb-2">Dias Ausente</label>
                  <input 
                    type="number" 
                    className="w-full border p-2 rounded" 
                    value={formData.dias_ausente}
                    onChange={e => setFormData({...formData, dias_ausente: Number(e.target.value)})}
                    required 
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold mb-2">Horário</label>
                  <input 
                    type="time" 
                    className="w-full border p-2 rounded" 
                    value={formData.horario}
                    onChange={e => setFormData({...formData, horario: e.target.value})}
                    required 
                  />
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Mensagem</label>
                <textarea 
                  className="w-full border p-2 rounded bg-gray-50" 
                  rows={3}
                  value={formData.mensagem}
                  onChange={e => setFormData({...formData, mensagem: e.target.value})}
                  required
                />
              </div>
              <div className="flex justify-end gap-2">
                <button 
                  type="button" 
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                >
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
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