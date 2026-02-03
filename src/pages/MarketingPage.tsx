import React, { useState, useEffect, useCallback } from 'react';
import { Trash2, PauseCircle, PlayCircle, Calendar, X, Loader2 } from 'lucide-react';

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
  active: boolean;
}

interface CRMCard {
  id: number;
  paciente_nome: string;
  paciente_phone: string;
  ultima_interacao: string;
  status: string;
  campanha?: string;
  origem?: string;
}

interface CRMStage {
  id: number;
  nome: string;
  cor: string;
  cards: CRMCard[];
}

const MarketingPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'automation' | 'campaigns'>('automation');
  const [loading, setLoading] = useState(true);
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [crmBoard, setCrmBoard] = useState<CRMStage[]>([]);

  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [isCampaignModalOpen, setIsCampaignModalOpen] = useState(false);
  const [isAgendaModalOpen, setIsAgendaModalOpen] = useState(false);
  const [savingAgenda, setSavingAgenda] = useState(false);

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

  const [agendaForm, setAgendaForm] = useState({
    lead_id: 0,
    title: '',
    date: new Date().toISOString().split('T')[0],
    time: '09:00',
    description: ''
  });

  const API_URL = '/api/marketing';
  const token = localStorage.getItem('odonto_token');

  const fetchData = useCallback(async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      const resRules = await fetch(`${API_URL}/automations`, { headers });
      if (resRules.ok) setRules(await resRules.json());

      try {
        const resCamp = await fetch(`${API_URL}/campaigns`, { headers });
        if (resCamp.ok) setCampaigns(await resCamp.json());
      } catch (e) {}

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
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

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
    } catch (error) {
      window.alert('Erro ao salvar regra');
    }
  };

  const handleDeleteRule = async (id: number) => {
    if (!window.confirm('Apagar regra?')) return;
    await fetch(`${API_URL}/automations/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    fetchData();
  };

  const handleSaveCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/campaigns`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(campaignForm)
      });
      if (res.ok) fetchData();
      setIsCampaignModalOpen(false);
      setCampaignForm({ name: '', message: 'Olá! Vi a promoção... [ref:TOKEN]' });
      alert('Campanha criada! Link gerado.');
    } catch (error) {
      window.alert('Erro ao criar campanha');
    }
  };

  const handleDeleteCampaign = async (id: number) => {
    if (!window.confirm('Tem certeza?')) return;
    await fetch(`${API_URL}/campaigns/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    fetchData();
  };

  const handleToggleCampaign = async (id: number, currentStatus: boolean) => {
    await fetch(`${API_URL}/campaigns/${id}/status`, {
      method: 'PATCH',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ active: !currentStatus })
    });
    fetchData();
  };

  const openAgendaModal = (card: CRMCard) => {
    setAgendaForm({
      lead_id: card.id,
      title: `${card.paciente_nome} - ${card.campanha || 'Consulta'}`,
      date: new Date().toISOString().split('T')[0],
      time: '09:00',
      description: `Agendamento via CRM. Origem: ${card.origem || 'WhatsApp'}`
    });
    setIsAgendaModalOpen(true);
  };

  const handleSaveAgenda = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingAgenda(true);
    try {
      const start = `${agendaForm.date}T${agendaForm.time}:00`;
      const res = await fetch('/api/appointments', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: agendaForm.title,
          description: agendaForm.description,
          start: start,
          lead_id: agendaForm.lead_id,
          status: 'scheduled'
        })
      });
      if (res.ok) {
        alert('Agendamento realizado com sucesso!');
        setIsAgendaModalOpen(false);
      }
    } catch (error) {
      alert('Erro ao agendar');
    } finally {
      setSavingAgenda(false);
    }
  };

  const getColorClass = (cor: string) => {
    const map: any = {
      yellow: 'border-yellow-400 bg-yellow-50',
      blue: 'border-blue-400 bg-blue-50',
      green: 'border-green-400 bg-green-50',
      red: 'border-red-400 bg-red-50'
    };
    return map[cor] || 'border-gray-200';
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen text-gray-800">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800">📢 Marketing & CRM</h1>
        <p className="text-gray-500">Gerencie robôs de retorno, campanhas de links e seu funil de vendas.</p>
      </div>

      <div className="flex gap-4 border-b border-gray-200 mb-6">
        <button onClick={() => setActiveTab('automation')} className={`pb-3 px-4 font-bold transition ${activeTab === 'automation' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>🤖 Robôs de Recall</button>
        <button onClick={() => setActiveTab('campaigns')} className={`pb-3 px-4 font-bold transition ${activeTab === 'campaigns' ? 'text-green-600 border-b-2 border-green-600' : 'text-gray-500 hover:text-gray-700'}`}>🔗 Campanhas & Links</button>
      </div>

      {activeTab === 'automation' && (
        <div className="mb-10 animate-fade-in">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-700">Regras Ativas</h3>
            <button onClick={() => setIsRuleModalOpen(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow hover:bg-blue-700 transition">+ Nova Regra</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {rules.map(rule => (
              <div key={rule.id} className="bg-white p-4 rounded-lg shadow border relative group hover:shadow-md transition">
                <button onClick={() => handleDeleteRule(rule.id)} className="absolute top-2 right-2 text-gray-300 hover:text-red-500"><Trash2 size={16} /></button>
                <h3 className="font-bold text-blue-600">{rule.nome}</h3>
                <p className="text-sm text-gray-600">🕒 {rule.horario} | 📅 {rule.dias_ausente} dias ausente</p>
                <div className="mt-2 text-xs bg-gray-50 p-2 rounded text-gray-700 italic border border-gray-100">"{rule.mensagem}"</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'campaigns' && (
        <div className="mb-10 animate-fade-in">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold text-gray-700">Campanhas de Links</h3>
            <button onClick={() => setIsCampaignModalOpen(true)} className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow hover:bg-green-700 transition">+ Criar Campanha</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {campaigns.map(camp => (
              <div key={camp.id} className={`bg-white p-4 rounded-lg shadow border border-green-50 relative group hover:shadow-md transition ${!camp.active ? 'opacity-75 grayscale' : ''}`}>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-bold text-green-700">{camp.name}</h3>
                    {!camp.active && <span className="text-[10px] bg-gray-200 text-gray-600 px-1 rounded uppercase font-bold">Pausada</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleToggleCampaign(camp.id, camp.active)} className="p-1 rounded hover:bg-gray-100 text-yellow-500">{camp.active ? <PauseCircle size={18} /> : <PlayCircle size={18} />}</button>
                    <button onClick={() => handleDeleteCampaign(camp.id)} className="p-1 rounded text-gray-300 hover:text-red-500"><Trash2 size={18} /></button>
                    <img src={camp.qr_code_url} alt="QR" className="w-10 h-10 border rounded p-1 ml-1" />
                  </div>
                </div>
                <div className="flex gap-4 text-xs text-gray-500 border-t pt-2">
                  <div className="text-center flex-1"><strong className="block text-lg text-gray-800">{camp.clicks || 0}</strong> Cliques</div>
                  <div className="text-center flex-1 border-l"><strong className="block text-lg text-green-600">{camp.leads || 0}</strong> Leads</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="border-t pt-8">
        <h3 className="text-2xl font-bold mb-6 text-slate-800">📊 Funil de Recuperação (CRM)</h3>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {crmBoard.map(stage => (
            <div key={stage.id} className="min-w-[300px] bg-gray-100 p-4 rounded-xl">
              <div className="font-bold text-gray-600 mb-4 flex justify-between uppercase text-sm border-b pb-2">
                {stage.nome} <span className="bg-gray-300 px-2 rounded-full text-xs text-gray-700 flex items-center">{stage.cards.length}</span>
              </div>
              <div className="space-y-3">
                {stage.cards.map(card => (
                  <div key={card.id} className={`bg-white p-4 rounded-lg shadow-sm border-l-4 group relative ${getColorClass(stage.cor)}`}>
                    <button 
                      onClick={() => openAgendaModal(card)}
                      className="absolute top-2 right-2 p-1.5 bg-blue-50 text-blue-600 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-blue-100"
                      title="Agendar"
                    >
                      <Calendar size={14} />
                    </button>
                    <div className="font-bold text-gray-800">{card.paciente_nome}</div>
                    {card.campanha && <div className="text-[11px] text-blue-600 font-medium mt-1">Campanha: {card.campanha}</div>}
                    <div className="text-xs text-gray-500 flex justify-between mt-2">
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

      {/* MODAL AGENDAR */}
      {isAgendaModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold text-xl text-gray-800">Agendar Lead</h2>
              <button onClick={() => setIsAgendaModalOpen(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleSaveAgenda} className="space-y-4">
              <input className="w-full border p-3 rounded-lg" value={agendaForm.title} onChange={e => setAgendaForm({...agendaForm, title: e.target.value})} required />
              <div className="flex gap-3">
                <input type="date" className="w-full border p-3 rounded-lg" value={agendaForm.date} onChange={e => setAgendaForm({...agendaForm, date: e.target.value})} required />
                <input type="time" className="w-full border p-3 rounded-lg" value={agendaForm.time} onChange={e => setAgendaForm({...agendaForm, time: e.target.value})} required />
              </div>
              <textarea className="w-full border p-3 rounded-lg" rows={2} value={agendaForm.description} onChange={e => setAgendaForm({...agendaForm, description: e.target.value})} />
              <button type="submit" disabled={savingAgenda} className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold flex justify-center items-center gap-2">
                {savingAgenda ? <Loader2 className="animate-spin" /> : 'Confirmar Agendamento'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* MODAL REGRA */}
      {isRuleModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="font-bold text-xl mb-4 text-gray-800">Nova Regra de Recall</h2>
            <form onSubmit={handleSaveRule} className="space-y-4">
              <input placeholder="Nome da Regra" className="w-full border p-3 rounded-lg" value={ruleForm.nome} onChange={e => setRuleForm({ ...ruleForm, nome: e.target.value })} required />
              <div className="flex gap-3">
                <input type="number" className="w-full border p-3 rounded-lg" value={ruleForm.dias_ausente} onChange={e => setRuleForm({ ...ruleForm, dias_ausente: Number(e.target.value) })} required />
                <input type="time" className="w-full border p-3 rounded-lg" value={ruleForm.horario} onChange={e => setRuleForm({ ...ruleForm, horario: e.target.value })} required />
              </div>
              <textarea className="w-full border p-3 rounded-lg" rows={3} value={ruleForm.mensagem} onChange={e => setRuleForm({ ...ruleForm, mensagem: e.target.value })} required />
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setIsRuleModalOpen(false)} className="px-4 py-2 text-gray-600">Cancelar</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold">Salvar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL CAMPANHA */}
      {isCampaignModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl w-full max-w-md shadow-2xl">
            <h2 className="font-bold text-xl mb-2 text-gray-800">Nova Campanha</h2>
            <form onSubmit={handleSaveCampaign} className="space-y-4">
              <input placeholder="Nome da Campanha" className="w-full border p-3 rounded-lg" value={campaignForm.name} onChange={e => setCampaignForm({ ...campaignForm, name: e.target.value })} required />
              <textarea className="w-full border p-3 rounded-lg" rows={3} value={campaignForm.message} onChange={e => setCampaignForm({ ...campaignForm, message: e.target.value })} required />
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setIsCampaignModalOpen(false)} className="px-4 py-2 text-gray-600">Cancelar</button>
                <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded-lg font-bold">Gerar Link</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketingPage;
