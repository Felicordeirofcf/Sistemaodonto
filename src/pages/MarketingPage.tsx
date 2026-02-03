import React, { useState, useEffect, useCallback } from 'react';

// --- TIPAGEM ---
interface AutomationRule {
  id: number;
  nome: string;
  dias_ausente: number;
  horario: string;
  mensagem: string;
  ativo: boolean;
}

interface CRMCard {
  id: number;
  paciente_nome: string;
  paciente_phone: string;
  ultima_interacao: string;
  status: string;
}

interface CRMStage {
  id: number;
  nome: string;
  cor: string;
  cards: CRMCard[];
}

const MarketingPage: React.FC = () => {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [crmBoard, setCrmBoard] = useState<CRMStage[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const [formData, setFormData] = useState({
    nome: '',
    dias_ausente: 180,
    horario: '09:00',
    mensagem: 'Olá {nome}, faz tempo que não te vemos! Vamos cuidar desse sorriso? 🦷'
  });

  const API_URL = '/api/marketing'; 
  const token = localStorage.getItem('odonto_token'); 

  // Função unificada para buscar tudo
  const fetchData = useCallback(async () => {
    try {
      // 1. Regras
      const resRules = await fetch(`${API_URL}/automations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resRules.ok) setRules(await resRules.json());

      // 2. CRM (Kanban)
      const resCRM = await fetch(`${API_URL}/crm/board`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resCRM.ok) setCrmBoard(await resCRM.json());

    } catch (error) {
      console.error("Erro ao atualizar dados:", error);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Atualiza a cada 30s
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_URL}/automations`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      setIsModalOpen(false);
      fetchData();
    } catch (error) { window.alert('Erro ao salvar'); }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Apagar regra?')) return;
    await fetch(`${API_URL}/automations/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    fetchData();
  };

  const getColorClass = (cor: string) => {
    const map: any = { yellow: 'border-yellow-400 bg-yellow-50', blue: 'border-blue-400 bg-blue-50', green: 'border-green-400 bg-green-50', red: 'border-red-400 bg-red-50' };
    return map[cor] || 'border-gray-200';
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen text-gray-800">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-slate-800">🤖 Automação de Recall</h1>
        <button onClick={() => setIsModalOpen(true)} className="bg-blue-600 text-white px-5 py-2 rounded-lg font-bold">+ Nova Regra</button>
      </div>

      {/* Regras */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {rules.map(rule => (
          <div key={rule.id} className="bg-white p-4 rounded-lg shadow border relative">
             <button onClick={() => handleDelete(rule.id)} className="absolute top-2 right-2 text-red-300 hover:text-red-500">🗑️</button>
             <h3 className="font-bold text-blue-600">{rule.nome}</h3>
             <p className="text-sm">🕒 {rule.horario} | 📅 {rule.dias_ausente} dias</p>
             <div className="mt-2 text-xs bg-green-50 p-2 rounded text-green-800 italic">"{rule.mensagem}"</div>
          </div>
        ))}
      </div>

      {/* Kanban CRM Real */}
      <h3 className="text-2xl font-bold mb-4">Funil de Recuperação (CRM)</h3>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {crmBoard.map(stage => (
          <div key={stage.id} className="min-w-[300px] bg-gray-100 p-4 rounded-xl">
            <div className="font-bold text-gray-600 mb-4 flex justify-between uppercase text-sm border-b pb-2">
              {stage.nome} <span className="bg-gray-300 px-2 rounded-full text-xs">{stage.cards.length}</span>
            </div>
            <div className="space-y-3">
              {stage.cards.length === 0 && <div className="text-center text-gray-400 text-xs italic">Vazio</div>}
              {stage.cards.map(card => (
                <div key={card.id} className={`bg-white p-4 rounded-lg shadow-sm border-l-4 ${getColorClass(stage.cor)}`}>
                  <div className="font-bold">{card.paciente_nome}</div>
                  <div className="text-xs text-gray-500 flex justify-between mt-1">
                    <span>{card.paciente_phone}</span>
                    <span>{card.ultima_interacao}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Modal - Simplificado para economizar espaço */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-96">
            <h2 className="font-bold text-xl mb-4">Nova Regra</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <input placeholder="Nome" className="w-full border p-2 rounded" onChange={e => setFormData({...formData, nome: e.target.value})} required />
              <div className="flex gap-2">
                <input type="number" placeholder="Dias" className="w-full border p-2 rounded" onChange={e => setFormData({...formData, dias_ausente: Number(e.target.value)})} required />
                <input type="time" className="w-full border p-2 rounded" onChange={e => setFormData({...formData, horario: e.target.value})} required />
              </div>
              <textarea placeholder="Mensagem" className="w-full border p-2 rounded" rows={3} onChange={e => setFormData({...formData, mensagem: e.target.value})} required />
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-gray-600">Cancelar</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">Salvar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketingPage;