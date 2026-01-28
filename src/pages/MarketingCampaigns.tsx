import { useState, useEffect } from 'react';
import { 
  MessageSquare, Zap, AlertCircle, Megaphone, 
  Sparkles, Play, Loader2, Target, BarChart3,
  Facebook, RefreshCw, CheckCircle
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
  
  // Estados para Sincronização Meta
  const [metaData, setMetaData] = useState<{balance: number, ad_account_id: string, last_sync: string} | null>(null);
  const [syncing, setSyncing] = useState(false);
  
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

  // Função para Sincronizar Saldo Real/Fictício da Meta
  const handleMetaSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch('/api/marketing/meta/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        }
      });
      const data = await res.json();
      if (res.ok) setMetaData(data);
    } catch (e) {
      console.error("Erro ao sincronizar com Meta");
    } finally {
      setSyncing(false);
    }
  };

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
            <p className="text-blue-100 font-medium">Sincronize sua conta de anúncios e deixe nossa IA trabalhar por você.</p>
          </div>
          <Megaphone size={120} className="absolute -right-5 -bottom-5 text-white/10 -rotate-12" />
        </div>
        
        <div className="p-10 grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Card de Conexão e Saldo Meta */}
          <div className="space-y-6">
            <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Sincronização de Saldo</h3>
            {!metaData ? (
              <button 
                onClick={handleMetaSync}
                disabled={syncing}
                className="w-full py-5 bg-[#1877F2] text-white rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-3 hover:bg-[#166fe5] transition-all shadow-lg"
              >
                {syncing ? <Loader2 className="animate-spin" /> : <Facebook size={18} />}
                {syncing ? 'Conectando...' : 'Vincular Conta Facebook'}
              </button>
            ) : (
              <div className="p-6 bg-blue-50 rounded-[2rem] border border-blue-100 animate-in zoom-in duration-300">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[9px] font-black text-blue-600 uppercase tracking-widest">Saldo na Meta</span>
                  <CheckCircle size={16} className="text-blue-500" />
                </div>
                <h4 className="text-3xl font-black text-blue-900 tracking-tighter">R$ {metaData.balance.toFixed(2)}</h4>
                <p className="text-[9px] text-blue-400 font-bold mt-2 uppercase">Conta: {metaData.ad_account_id}</p>
              </div>
            )}
            
            <button 
              onClick={handleActivateAds}
              disabled={adsLoading || adsActive || !metaData}
              className={`w-full py-5 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-3 ${
                adsActive ? 'bg-green-500 text-white shadow-green-100' : 'bg-gray-900 text-white shadow-gray-200 hover:bg-black'
              } disabled:opacity-30`}
            >
              {adsLoading ? <Loader2 className="animate-spin" /> : adsActive ? <Zap /> : <Play />}
              {adsLoading ? 'Iniciando...' : adsActive ? 'IA de Anúncios Ativa' : 'Ativar Piloto Automático'}
            </button>
          </div>

          <div className="bg-gray-50 rounded-[2.5rem] p-8 space-y-4 border border-gray-100">
            <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Configurar Gasto Mensal</h3>
            <div className="flex items-end gap-1 mb-4">
              <span className="text-3xl font-black text-gray-900 tracking-tighter">R$ {budget}</span>
              <span className="text-[10px] font-bold text-gray-400 mb-1">/mês</span>
            </div>
            <input 
              type="range" min="300" max="5000" step="100"
              className="w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer accent-blue-600"
              value={budget} onChange={(e) => setBudget(Number(e.target.value))}
            />
            <div className="pt-4 space-y-3">
              <div className="flex justify-between font-bold text-[11px] uppercase text-gray-400">
                <span>Expectativa Leads</span>
                <span className="text-blue-600">~{Math.floor(budget / 12)} pacientes</span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center">
            <div className="w-full max-w-[200px] border-4 border-gray-100 rounded-[2rem] p-2 bg-white shadow-xl rotate-3">
               <div className="aspect-[4/5] bg-gray-50 rounded-[1.5rem] flex items-center justify-center overflow-hidden">
                  <img src="https://images.unsplash.com/photo-1606811841689-23dfddce3e95?w=400" className="object-cover h-full w-full opacity-80" alt="Ads Preview" />
               </div>
               <div className="mt-3 text-center text-[8px] font-black uppercase text-blue-600 tracking-widest">Criativo Gerado por IA</div>
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
              <h2 className="font-black text-xl tracking-tight">Recall Interno</h2>
              <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Reativação de Pacientes</p>
            </div>
          </div>
          <div className="space-y-6">
            <div className="flex justify-between items-center px-2">
              <span className="text-xs font-bold text-gray-400 uppercase">Candidatos</span>
              <span className="font-black text-2xl text-blue-600">{candidates.length}</span>
            </div>
            <button className="w-full py-4 bg-gray-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-gray-200 hover:bg-black transition-all active:scale-95">
              Iniciar Disparos
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-8 border-b border-gray-50 bg-gray-50/30 text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">
            Lista de Reativação Automática
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-50">
                  <th className="px-8 py-5">Nome do Paciente</th>
                  <th className="px-8 py-5">Última Visita</th>
                  <th className="px-8 py-5 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 font-bold">
                {candidates.length > 0 ? candidates.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50/50 transition-colors group">
                    <td className="px-8 py-6">
                      <div className="text-gray-800 text-sm">{p.name}</div>
                      <div className="text-[9px] text-gray-400 uppercase tracking-tighter">{p.phone}</div>
                    </td>
                    <td className="px-8 py-6 text-xs text-gray-400">{p.last_visit}</td>
                    <td className="px-8 py-6 text-right">
                      <button 
                        onClick={() => triggerBot(p)}
                        className="inline-flex items-center gap-2 bg-green-50 text-green-600 px-5 py-2.5 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-green-600 hover:text-white transition-all shadow-sm"
                      >
                        <MessageSquare size={14}/> Reativar WhatsApp
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={3} className="px-8 py-16 text-center text-gray-300 uppercase text-[10px] font-black tracking-widest italic">
                      Todos os pacientes estão com as revisões em dia.
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