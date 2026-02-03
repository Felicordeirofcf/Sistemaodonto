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

interface Campaign {
  id: number;
  name: string;
  tracking_code: string;
  tracking_url: string;
  qr_code_url: string;
  clicks: number;
  leads: number;
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
  // --- ESTADOS GERAIS ---
  const [activeTab, setActiveTab] = useState<'automation' | 'campaigns'>('automation');
  const [loading, setLoading] = useState(true);
  
  // Dados
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [crmBoard, setCrmBoard] = useState<CRMStage[]>([]);

  // Modais
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [isCampaignModalOpen, setIsCampaignModalOpen] = useState(false);
  
  // Forms
  const [ruleForm, setRuleForm] = useState({
    nome: '',
    dias_ausente: 180,
    horario: '09:00',
    mensagem: 'Olá {nome}, faz tempo que não te vemos! Vamos cuidar desse sorriso? 🦷'
  });

  const [campaignForm, setCampaignForm] = useState({
    name: '',
    message: 'Olá! Vi a promoção e quero agendar. [ref:TOKEN]'
  });

  const API_URL = '/api/marketing'; 
  const token = localStorage.getItem('odonto_token'); 

  // --- BUSCAR DADOS (UNIFICADO) ---
  const fetchData = useCallback(async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };

      // 1. Regras de Automação
      const resRules = await fetch(`${API_URL}/automations`, { headers });
      if (resRules.ok) setRules(await resRules.json());

      // 2. Campanhas (Tenta buscar se o endpoint GET existir, senão ignora)
      // Nota: Você precisará criar o endpoint GET /campaigns no backend para listar na tela
      try {
        const resCamp = await fetch(`${API_URL}/campaigns`, { headers });
        if (resCamp.ok) setCampaigns(await resCamp.json());
      } catch (e) { /* Endpoint pode não existir ainda */ }

      // 3. CRM (Kanban)
      const resCRM = await fetch(`${API_URL}/crm/board`, { headers });
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

  // --- HANDLERS AUTOMAÇÃO ---
  const handleSaveRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`${API_URL}/automations`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(ruleForm)
      });
      setIsRuleModalOpen(false);
      fetchData();
      setRuleForm({ nome: '', dias_ausente: 180, horario: '09:00', mensagem: 'Olá {nome}...' });
    } catch (error) { window.alert('Erro ao salvar regra'); }
  };

  const handleDeleteRule = async (id: number) => {
    if (!window.confirm('Apagar regra?')) return;
    await fetch(`${API_URL}/automations/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    fetchData();
  };

  // --- HANDLERS CAMPANHA ---
  const handleSaveCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/campaigns`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(campaignForm)
      });
      
      if(res.ok) {
        // Se o backend retornar a campanha criada, adicionamos manualmente para feedback imediato
        const newCamp = await res.json();
        setCampaigns(prev => [newCamp, ...prev]); 
      }
      
      setIsCampaignModalOpen(false);
      setCampaignForm({ name: '', message: 'Olá! Vi a promoção... [ref:TOKEN]' });
      alert('Campanha criada! Link gerado.');
      fetchData(); // Tenta recarregar
    } catch (error) { window.alert('Erro ao criar campanha'); }
  };

  const copyLink = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Link copiado!');
  };

  // Helper de UI
  const getColorClass = (cor: string) => {
    const map: any = { yellow: 'border-yellow-400 bg-yellow-50', blue: 'border-blue-400 bg-blue-50', green: 'border-green-400 bg-green-50', red: 'border-red-400 bg-red-50' };
    return map[cor] || 'border-gray-200';
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen text-gray-800">
      
      {/* CABEÇALHO */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800">📢 Marketing & CRM</h1>
        <p className="text-gray-500">Gerencie robôs de retorno, campanhas de links e seu funil de vendas em um só lugar.</p>
      </div>

      {/* ABAS DE NAVEGAÇÃO */}
      <div className="flex gap-4 border-b border-gray-200 mb-6">
        <button 
          onClick={() => setActiveTab('automation')}
          className={`pb-3 px-4 font-bold transition ${activeTab === 'automation' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
        >
          🤖 Robôs de Recall
        </button>
        <button 
          onClick={() => setActiveTab('campaigns')}
          className={`pb-3 px-4 font-bold transition ${activeTab === 'campaigns' ? 'text-green-600 border-b-2 border-green-600' : 'text-gray-500 hover:text-gray-700'}`}
        >
          🔗 Campanhas & Links
        </button>
      </div>

      {/* CONTEÚDO DA ABA: AUTOMAÇÃO */}
      {activeTab === 'automation' && (
        <div className="mb-10 animate-fade-in">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-700">Regras Ativas</h3>
            <button onClick={() => setIsRuleModalOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow hover:bg-blue-700 transition">+ Nova Regra</button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {rules.length === 0 && <p className="text-gray-400 col-span-3 text-center py-8 bg-white rounded border border-dashed">Nenhuma regra de automação criada.</p>}
            {rules.map(rule => (
              <div key={rule.id} className="bg-white p-4 rounded-lg shadow border relative group hover:shadow-md transition">
                 <button onClick={() => handleDeleteRule(rule.id)} className="absolute top-2 right-2 text-gray-300 hover:text-red-500">🗑️</button>
                 <h3 className="font-bold text-blue-600">{rule.nome}</h3>
                 <p className="text-sm text-gray-600">🕒 {rule.horario} | 📅 {rule.dias_ausente} dias ausente</p>
                 <div className="mt-2 text-xs bg-gray-50 p-2 rounded text-gray-700 italic border border-gray-100">"{rule.mensagem}"</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CONTEÚDO DA ABA: CAMPANHAS */}
      {activeTab === 'campaigns' && (
        <div className="mb-10 animate-fade-in">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-700">Campanhas de Links e QR Code</h3>
            <button onClick={() => setIsCampaignModalOpen(true)} className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow hover:bg-green-700 transition">+ Criar Campanha</button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {campaigns.length === 0 && <p className="text-gray-400 col-span-3 text-center py-8 bg-white rounded border border-dashed">Nenhuma campanha criada. Crie uma para gerar links rastreáveis.</p>}
            {campaigns.map(camp => (
              <div key={camp.id} className="bg-white p-4 rounded-lg shadow border border-green-50 relative group hover:shadow-md transition">
                 <div className="flex justify-between items-start mb-3">
                    <h3 className="font-bold text-green-700">{camp.name}</h3>
                    <img src={camp.qr_code_url} alt="QR" className="w-12 h-12 border rounded p-1" />
                 </div>
                 
                 <div className="bg-gray-50 rounded p-2 mb-3 flex items-center justify-between border">
                    <span className="text-xs text-gray-600 truncate max-w-[180px]">{camp.tracking_url}</span>
                    <button onClick={() => copyLink(camp.tracking_url)} className="text-xs bg-white border px-2 py-1 rounded font-bold hover:bg-gray-100">Copiar</button>
                 </div>

                 <div className="flex gap-4 text-xs text-gray-500 border-t pt-2">
                    <div className="text-center flex-1">
                      <strong className="block text-lg text-gray-800">{camp.clicks || 0}</strong> Cliques
                    </div>
                    <div className="text-center flex-1 border-l">
                      <strong className="block text-lg text-green-600">{camp.leads || 0}</strong> Leads
                    </div>
                 </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* KANBAN CRM (SEMPRE VISÍVEL NO FINAL POIS RECEBE DADOS DE AMBOS) */}
      <div className="border-t pt-8">
        <h3 className="text-2xl font-bold mb-6 text-slate-800">📊 Funil de Recuperação (CRM)</h3>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {crmBoard.map(stage => (
            <div key={stage.id} className="min-w-[300px] bg-gray-100 p-4 rounded-xl">
              <div className="font-bold text-gray-600 mb-4 flex justify-between uppercase text-sm border-b pb-2">
                {stage.nome} <span className="bg-gray-300 px-2 rounded-full text-xs text-gray-700 flex items-center">{stage.cards.length}</span>
              </div>
              <div className="space-y-3">
                {stage.cards.length === 0 && <div className="text-center text-gray-400 text-xs italic py-4">Nenhum paciente</div>}
                {stage.cards.map(card => (
                  <div key={card.id} className={`bg-white p-4 rounded-lg shadow-sm border-l-4 cursor-pointer hover:shadow-md transition ${getColorClass(stage.cor)}`}>
                    <div className="font-bold text-gray-800">{card.paciente_nome}</div>
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
      </div>

      {/* MODAL: NOVA REGRA (RECALL) */}
      {isRuleModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="font-bold text-xl mb-4 text-gray-800">Nova Regra de Recall</h2>
            <form onSubmit={handleSaveRule} className="space-y-4">
              <input placeholder="Nome da Regra" className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" value={ruleForm.nome} onChange={e => setRuleForm({...ruleForm, nome: e.target.value})} required />
              <div className="flex gap-3">
                <input type="number" placeholder="Dias Ausente" className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" value={ruleForm.dias_ausente} onChange={e => setRuleForm({...ruleForm, dias_ausente: Number(e.target.value)})} required />
                <input type="time" className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" value={ruleForm.horario} onChange={e => setRuleForm({...ruleForm, horario: e.target.value})} required />
              </div>
              <textarea placeholder="Mensagem" className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" rows={3} value={ruleForm.mensagem} onChange={e => setRuleForm({...ruleForm, mensagem: e.target.value})} required />
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setIsRuleModalOpen(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold shadow">Salvar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: NOVA CAMPANHA (LINKS) */}
      {isCampaignModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="font-bold text-xl mb-2 text-gray-800">Nova Campanha de Link</h2>
            <p className="text-sm text-gray-500 mb-4">Gera um Link e QR Code para WhatsApp.</p>
            <form onSubmit={handleSaveCampaign} className="space-y-4">
              <input placeholder="Nome da Campanha (ex: Verão)" className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-green-500 outline-none" value={campaignForm.name} onChange={e => setCampaignForm({...campaignForm, name: e.target.value})} required />
              <div>
                <label className="text-xs font-bold text-gray-500 uppercase">Mensagem Inicial (WhatsApp)</label>
                <textarea className="w-full border p-3 rounded-lg focus:ring-2 focus:ring-green-500 outline-none mt-1" rows={3} value={campaignForm.message} onChange={e => setCampaignForm({...campaignForm, message: e.target.value})} required />
                <p className="text-[10px] text-orange-600 mt-1">⚠️ O código de rastreio [ref:TOKEN] será adicionado automaticamente.</p>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setIsCampaignModalOpen(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
                <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-bold shadow">Gerar Link</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default MarketingPage;