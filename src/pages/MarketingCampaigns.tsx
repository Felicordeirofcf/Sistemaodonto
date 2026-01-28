import { useState, useEffect } from 'react';
import { 
  MessageSquare, Zap, AlertCircle, Megaphone, 
  Sparkles, Play, Loader2, Target, BarChart3 
} from 'lucide-react';

interface RecallPatient {
  id: number;
  name: string;
  phone: string;
  last_visit: string;
  suggested_msg: string;
}

export function MarketingCampaigns() {
  const [candidates, setCandidates] = useState<RecallPatient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  
  // Estados para a Automação de Anúncios
  const [budget, setBudget] = useState(300);
  const [adsActive, setAdsActive] = useState(false);
  const [adsLoading, setAdsLoading] = useState(false);

  useEffect(() => {
    fetch('/api/marketing/campaign/recall', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
    .then(res => {
      if (!res.ok) throw new Error('Falha na API');
      return res.json();
    })
    .then(data => {
      if (Array.isArray(data)) setCandidates(data);
    })
    .catch((err) => {
      console.error(err);
      setError(true);
    })
    .finally(() => setLoading(false));
  }, []);

  const handleActivateAds = async () => {
    setAdsLoading(true);
    try {
      const res = await fetch('/api/marketing/campaign/activate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        },
        body: JSON.stringify({ budget })
      });
      if (res.ok) setAdsActive(true);
    } catch (e) {
      alert("Erro ao ativar OdontoAds.");
    } finally {
      setAdsLoading(false);
    }
  };

  const triggerBot = (patient: RecallPatient) => {
    const whatsappUrl = `https://wa.me/${patient.phone}?text=${encodeURIComponent(patient.suggested_msg)}`;
    window.open(whatsappUrl, '_blank');
  };

  if (loading) return (
    <div className="h-screen w-full flex items-center justify-center bg-gray-50">
      <Loader2 className="animate-spin text-blue-600" size={48} />
    </div>
  );

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <header className="mb-10">
        <h1 className="text-4xl font-black text-gray-900 tracking-tight flex items-center gap-3">
          <Sparkles className="text-blue-600" size={36} /> Automação de Vendas
        </h1>
        <p className="text-gray-500 font-medium mt-2">IA para captar novos leads e reativar pacientes antigos.</p>
      </header>

      {/* SEÇÃO 1: ODONTOADS (CRESCIMENTO EXTERNO) */}
      <div className="bg-white rounded-[3rem] shadow-sm border border-gray-100 overflow-hidden mb-10">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-10 text-white relative">
          <div className="relative z-10 max-w-2xl">
            <h2 className="text-2xl font-black uppercase tracking-widest mb-2">OdontoAds Inteligente</h2>
            <p className="text-blue-100 font-medium">Atraia pacientes novos automaticamente no Instagram e Facebook.</p>
          </div>
          <Megaphone size={120} className="absolute -right-5 -bottom-5 text-white/10 -rotate-12" />
        </div>
        
        <div className="p-10 grid grid-cols-1 lg:grid-cols-3 gap-10">
          <div className="space-y-6">
            <label className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Orçamento Mensal</label>
            <div className="flex items-end gap-2">
              <span className="text-4xl font-black text-gray-900 tracking-tighter text-blue-600">R$ {budget}</span>
              <span className="text-gray-400 font-bold mb-1">/mês</span>
            </div>
            <input 
              type="range" min="300" max="5000" step="100"
              className="w-full h-2 bg-gray-100 rounded-full appearance-none cursor-pointer accent-blue-600"
              value={budget} onChange={(e) => setBudget(Number(e.target.value))}
            />
            <button 
              onClick={handleActivateAds}
              disabled={adsLoading || adsActive}
              className={`w-full py-5 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-3 ${
                adsActive ? 'bg-green-500 text-white shadow-green-100' : 'bg-blue-600 text-white shadow-blue-100 hover:bg-blue-700 shadow-xl'
              }`}
            >
              {adsLoading ? <Loader2 className="animate-spin" /> : adsActive ? <Zap /> : <Play />}
              {adsLoading ? 'Sincronizando...' : adsActive ? 'IA de Anúncios Ativa' : 'Iniciar Crescimento'}
            </button>
          </div>

          <div className="bg-gray-50 rounded-[2.5rem] p-8 space-y-4 border border-gray-100">
            <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Previsão de Resultados</h3>
            <div className="flex justify-between font-bold text-sm">
              <span className="text-gray-500 flex items-center gap-2"><Target size={14}/> Alcance</span>
              <span className="text-gray-900">~{budget * 15} pessoas</span>
            </div>
            <div className="flex justify-between font-bold text-sm">
              <span className="text-gray-500 flex items-center gap-2"><BarChart3 size={14}/> Leads</span>
              <span className="text-blue-600">~{Math.floor(budget / 10)} contatos</span>
            </div>
          </div>

          <div className="flex items-center justify-center">
            <div className="w-full max-w-[200px] border-4 border-gray-100 rounded-[2rem] p-2 bg-white shadow-xl rotate-3">
               <div className="aspect-[4/5] bg-gray-50 rounded-[1.5rem] flex items-center justify-center overflow-hidden">
                  <img src="https://images.unsplash.com/photo-1606811841689-23dfddce3e95?w=400" className="object-cover h-full w-full opacity-80" alt="Ads Preview" />
               </div>
               <div className="mt-3 text-center text-[8px] font-black uppercase text-blue-600">Anúncio IA Gerado</div>
            </div>
          </div>
        </div>
      </div>

      {/* SEÇÃO 2: RECALL IA (REATIVAÇÃO DE BASE) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 h-fit">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-4 bg-blue-50 text-blue-600 rounded-2xl shadow-sm"><Zap size={28}/></div>
            <div>
              <h2 className="font-black text-xl tracking-tight">Robô de Reativação</h2>
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Recall Interno</p>
            </div>
          </div>
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <span className="text-xs font-bold text-gray-400 uppercase">Pacientes Sumidos</span>
              <span className="font-black text-2xl text-blue-600">{candidates.length}</span>
            </div>
            <div className="p-4 bg-green-50 rounded-2xl border border-green-100 flex justify-between items-center">
              <span className="text-[10px] font-black text-green-700 uppercase">Vagas Amanhã</span>
              <span className="text-[10px] font-black text-green-600 border border-green-200 px-3 py-1 rounded-full bg-white">LIVRE</span>
            </div>
            <button className="w-full py-4 bg-gray-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-gray-200 hover:bg-black transition-all">
              Ativar Disparo Automático
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-8 border-b border-gray-50 bg-gray-50/30 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">
            Lista de Reativação (Prontos para Contato)
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-50">
                  <th className="px-8 py-5">Paciente</th>
                  <th className="px-8 py-5">Última Visita</th>
                  <th className="px-8 py-5 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 font-bold">
                {candidates.length > 0 ? candidates.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50/50 transition-colors group">
                    <td className="px-8 py-6">
                      <div className="text-gray-800">{p.name}</div>
                      <div className="text-[10px] text-gray-400">{p.phone}</div>
                    </td>
                    <td className="px-8 py-6 text-xs text-gray-400">{p.last_visit}</td>
                    <td className="px-8 py-6 text-right">
                      <button 
                        onClick={() => triggerBot(p)}
                        className="inline-flex items-center gap-2 bg-green-50 text-green-600 px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-green-600 hover:text-white transition-all shadow-sm"
                      >
                        <MessageSquare size={14}/> Reativar no Zap
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={3} className="px-8 py-16 text-center text-gray-300 uppercase text-[10px] font-black tracking-widest italic">
                      Nenhum paciente pendente de reativação no momento.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}