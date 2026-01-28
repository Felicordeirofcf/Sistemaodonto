import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { 
  MoreHorizontal, Plus, Phone, X, Loader2, 
  Facebook, Target, TrendingUp, DollarSign, RefreshCw, CheckCircle2,
  Instagram, Wand2, Copy, Image as ImageIcon, AlertTriangle, LogOut
} from 'lucide-react';

declare global {
  interface Window {
    fbAsyncInit: () => void;
    FB: any;
  }
}

interface Lead { id: number; name: string; source: string; phone?: string; status: string; notes?: string; }
interface IgMedia { id: string; media_url: string; thumbnail_url?: string; caption?: string; media_type: string; }

const COLUMNS = {
  new: { title: 'Novos Leads', color: 'border-blue-500', headerColor: 'text-blue-600', bg: 'bg-blue-50' },
  contacted: { title: 'Agendamento Tentado', color: 'border-yellow-500', headerColor: 'text-yellow-600', bg: 'bg-yellow-50' },
  scheduled: { title: 'Consulta Agendada', color: 'border-green-500', headerColor: 'text-green-600', bg: 'bg-green-50' },
  treating: { title: 'Em Tratamento', color: 'border-purple-500', headerColor: 'text-purple-600', bg: 'bg-purple-50' }
};

export function MarketingCRM() {
  
  const [activeTab, setActiveTab] = useState<'funnel' | 'creative'>('funnel');
  const [mediaSource, setMediaSource] = useState<'instagram' | 'facebook'>('instagram');
  const [leads, setLeads] = useState<Lead[]>([]);
  const [mediaList, setMediaList] = useState<IgMedia[]>([]);
  const [selectedMedia, setSelectedMedia] = useState<IgMedia | null>(null);
  const [aiCaption, setAiCaption] = useState('');
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [igError, setIgError] = useState<string | null>(null);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newLead, setNewLead] = useState({ name: '', phone: '', source: 'Manual', notes: '' });
  
  const [isConnected, setIsConnected] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true); 
  const [adsStats, setAdsStats] = useState({ spend: 0.0, clicks: 0, cpc: 0.0 });

  useEffect(() => {
    const token = localStorage.getItem('odonto_token');
    fetch('/api/marketing/leads', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(res => res.json()).then(data => { if (Array.isArray(data)) setLeads(data); })
      .catch(console.error).finally(() => setLoading(false));

    window.fbAsyncInit = function() {
        window.FB.init({ appId: '928590639502117', cookie: true, xfbml: true, version: 'v19.0' });
    };
    (function(d, s, id){
       var js, fjs = d.getElementsByTagName(s)[0];
       if (d.getElementById(id)) {return;}
       js = d.createElement(s); js.id = id;
       // @ts-ignore
       js.src = "https://connect.facebook.net/pt_BR/sdk.js";
       // @ts-ignore
       fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));

    checkMetaConnection();
  }, []);

  const checkMetaConnection = async () => {
    try {
        const token = localStorage.getItem('odonto_token');
        if (!token) return;
        const res = await fetch('/api/marketing/meta/sync', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const data = await res.json();
            setIsConnected(true);
            if (data.spend !== undefined) {
                setAdsStats({ spend: data.spend, clicks: data.clicks, cpc: data.cpc });
            }
        } else {
            if(res.status === 401) setIsConnected(false);
        }
    } catch (e) { console.log("Sem conexão Meta"); }
    finally { setCheckingAuth(false); }
  };

  const handleFacebookLogin = () => {
    setAuthLoading(true);
    if (!window.FB) return alert("Erro no SDK Facebook");
    window.FB.login((response: any) => {
        if (response.authResponse) sendTokenToBackend(response.authResponse.accessToken);
        else setAuthLoading(false);
    }, { scope: 'ads_management,ads_read,leads_retrieval,instagram_basic,pages_show_list,pages_read_engagement' });
  };

  const sendTokenToBackend = async (fbToken: string) => {
    try {
        const res = await fetch('/api/marketing/meta/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` },
            body: JSON.stringify({ accessToken: fbToken })
        });
        if (res.ok) { 
            setIsConnected(true); 
            alert("Conectado com Sucesso!");
            checkMetaConnection(); 
        }
    } catch (error) { alert("Erro ao conectar."); } finally { setAuthLoading(false); }
  };

  // --- NOVA FUNÇÃO: DESCONECTAR ---
  const handleDisconnect = async () => {
    if (!window.confirm("Deseja realmente desconectar a conta do Facebook/Instagram?")) return;
    setAuthLoading(true);
    try {
        const res = await fetch('/api/marketing/meta/disconnect', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
        });
        if (res.ok) {
            setIsConnected(false);
            setAdsStats({ spend: 0.0, clicks: 0, cpc: 0.0 });
            setMediaList([]);
            alert("Desconectado com sucesso.");
        }
    } catch (e) { alert("Erro ao desconectar."); }
    finally { setAuthLoading(false); }
  };

  const fetchMedia = async (source: 'instagram' | 'facebook') => {
    if (!isConnected) return;
    setMediaLoading(true);
    setIgError(null);
    setMediaSource(source);
    
    try {
        const endpoint = source === 'instagram' ? '/api/marketing/instagram/media' : '/api/marketing/facebook/media';
        const res = await fetch(endpoint, {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
        });
        const data = await res.json();
        
        if (res.ok) {
            setMediaList(data);
        } else {
            setIgError(data.error || "Erro ao buscar mídia.");
            setMediaList([]);
        }
    } catch (e) { 
        setIgError("Falha na conexão."); 
    }
    finally { setMediaLoading(false); }
  };

  const generateAiCopy = async () => {
    if (!selectedMedia) return;
    setIsGenerating(true);
    try {
        const res = await fetch('/api/marketing/ai/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` },
            body: JSON.stringify({ caption: selectedMedia.caption, tone: 'persuasive' })
        });
        const data = await res.json();
        setAiCaption(data.suggestion);
    } catch (e) { alert("Erro na IA"); }
    finally { setIsGenerating(false); }
  };

  const handleCreateLead = async (e: React.FormEvent) => { 
      e.preventDefault(); 
      try {
        const res = await fetch('/api/marketing/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` },
            body: JSON.stringify({ ...newLead, status: 'new' })
        });
        const saved = await res.json();
        setLeads([...leads, saved]);
        setIsModalOpen(false);
        setNewLead({ name: '', phone: '', source: 'Manual', notes: '' });
      } catch(e) { alert("Erro ao criar"); }
  };

  const onDragEnd = async (result: DropResult) => { 
      if (!result.destination) return;
      const newStatus = result.destination.droppableId;
      const leadId = parseInt(result.draggableId);
      const oldLeads = [...leads];
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));
      try { await fetch(`/api/marketing/leads/${leadId}/move`, { method: 'PUT', headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`}, body: JSON.stringify({ status: newStatus }) }); } catch (e) { setLeads(oldLeads); }
  };
  const getColumnLeads = (status: string) => leads.filter(l => l.status === status);

  if (loading && !isConnected) return <div className="flex h-screen items-center justify-center bg-gray-50"><Loader2 className="animate-spin text-blue-600" size={48} /></div>;

  return (
    <div className="p-8 w-full h-screen overflow-hidden flex flex-col bg-gray-50 relative font-sans">
      
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-6 flex-shrink-0">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Marketing & Ads</h1>
          <p className="text-gray-500 font-medium">Automação de Leads e Criativos com IA.</p>
        </div>
        
        <div className="flex items-center gap-4">
            {/* TABS DE NAVEGAÇÃO */}
            <div className="flex bg-white p-1 rounded-xl border border-gray-200 shadow-sm">
                <button 
                    onClick={() => setActiveTab('funnel')}
                    className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'funnel' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}
                >
                    Funil de Vendas
                </button>
                <button 
                    onClick={() => { setActiveTab('creative'); fetchMedia('instagram'); }}
                    className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${activeTab === 'creative' ? 'bg-purple-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}
                >
                    <Wand2 size={14} /> Criador IA
                </button>
            </div>

            {/* BOTÃO NOVO LEAD MANUAL (MANTIDO!) */}
            <button onClick={() => setIsModalOpen(true)} className="px-6 py-3 bg-gray-900 text-white rounded-xl font-bold text-sm hover:bg-gray-800 flex items-center gap-2 shadow-xl shadow-gray-200 transition-all active:scale-95">
                <Plus size={18} /> Novo Lead
            </button>
        </div>
      </header>

      {/* --- ABA: FUNIL DE VENDAS --- */}
      {activeTab === 'funnel' && (
        <>
            <div className="mb-6 flex-shrink-0">
                {checkingAuth ? ( <div className="h-24 bg-gray-100 rounded-3xl animate-pulse"></div> ) : !isConnected ? (
                    <button onClick={handleFacebookLogin} disabled={authLoading} className="flex items-center gap-2 px-5 py-3 bg-[#1877F2] text-white rounded-xl font-bold shadow-lg hover:bg-[#166fe5]">
                        <Facebook size={20} /> {authLoading ? 'Conectando...' : 'Vincular Facebook & Instagram'}
                    </button>
                ) : (
                    <div className="flex justify-between items-start gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
                        {/* STATS */}
                        <div className="grid grid-cols-3 gap-4 flex-1">
                            <div className="bg-white p-4 rounded-2xl border border-blue-100 shadow-sm"><span className="text-[10px] uppercase text-gray-400 font-black">Investimento</span><div className="text-2xl font-black text-gray-800">R$ {adsStats.spend.toFixed(2)}</div></div>
                            <div className="bg-white p-4 rounded-2xl border border-purple-100 shadow-sm"><span className="text-[10px] uppercase text-gray-400 font-black">Cliques</span><div className="text-2xl font-black text-gray-800">{adsStats.clicks}</div></div>
                            <div className="bg-green-500 text-white p-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 font-bold cursor-pointer hover:bg-green-600 active:scale-95 transition-all" onClick={checkMetaConnection}>
                                <RefreshCw size={18} /> Sincronizar Tudo
                            </div>
                        </div>
                        
                        {/* BOTÃO DESCONECTAR (NOVO) */}
                        <button 
                            onClick={handleDisconnect} 
                            disabled={authLoading}
                            className="bg-red-50 text-red-600 border border-red-200 p-4 rounded-2xl shadow-sm flex items-center justify-center gap-2 font-bold cursor-pointer hover:bg-red-100 active:scale-95 transition-all h-full"
                        >
                            <LogOut size={18} />
                        </button>
                    </div>
                )}
            </div>
            
            <DragDropContext onDragEnd={onDragEnd}>
                <div className="flex-1 overflow-x-auto pb-4"><div className="flex gap-6 h-full min-w-[1200px]">
                    {Object.entries(COLUMNS).map(([id, cfg]) => (
                        <div key={id} className="flex flex-col bg-gray-200/30 rounded-[2rem] w-80 h-full border border-gray-200/50">
                            <div className={`bg-white p-4 rounded-t-[2rem] border-t-8 ${cfg.color} font-black text-xs uppercase ${cfg.headerColor}`}>{cfg.title}</div>
                            <Droppable droppableId={id}>{(p, s) => (<div {...p.droppableProps} ref={p.innerRef} className="flex-1 p-4 flex flex-col gap-3 overflow-y-auto">{getColumnLeads(id).map((item, idx) => (
                                <Draggable key={item.id} draggableId={String(item.id)} index={idx}>{(p, s) => (
                                    <div ref={p.innerRef} {...p.draggableProps} {...p.dragHandleProps} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100"><div className="font-bold text-sm">{item.name}</div><div className="text-xs text-gray-400 mt-1">{item.source}</div></div>
                                )}</Draggable>
                            ))}{p.placeholder}</div>)}</Droppable>
                        </div>
                    ))}
                </div></div>
            </DragDropContext>
        </>
      )}

      {/* --- ABA: CRIADOR IA --- */}
      {activeTab === 'creative' && (
        <div className="flex gap-6 h-full overflow-hidden">
            {/* Galeria */}
            <div className="w-2/3 bg-white rounded-[2rem] p-6 shadow-sm border border-gray-200 overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                        {mediaSource === 'instagram' ? <Instagram className="text-pink-600"/> : <Facebook className="text-blue-600"/>} 
                        Selecione um Post
                    </h3>
                    
                    {/* Botões de Troca de Fonte */}
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        <button onClick={() => fetchMedia('instagram')} className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${mediaSource === 'instagram' ? 'bg-white shadow text-pink-600' : 'text-gray-500'}`}>Instagram</button>
                        <button onClick={() => fetchMedia('facebook')} className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${mediaSource === 'facebook' ? 'bg-white shadow text-blue-600' : 'text-gray-500'}`}>Facebook</button>
                    </div>
                </div>
                
                {!isConnected ? (
                    <div className="h-64 flex flex-col items-center justify-center text-gray-400 bg-gray-50 rounded-2xl border-2 border-dashed">
                        <ImageIcon size={48} className="mb-2 opacity-50"/>
                        <p>Conecte as Redes Sociais na aba "Funil" primeiro.</p>
                    </div>
                ) : mediaLoading ? (
                    <div className="h-64 flex flex-col items-center justify-center text-gray-400"><Loader2 className="animate-spin mb-2 text-purple-600" size={32}/><p>Buscando fotos...</p></div>
                ) : igError ? (
                    <div className="bg-red-50 p-6 rounded-2xl border border-red-100 flex flex-col items-center text-center">
                        <AlertTriangle className="text-red-500 mb-2" size={32}/>
                        <h4 className="text-red-800 font-bold mb-1">Mídia não encontrada</h4>
                        <p className="text-red-600 text-sm mb-4 max-w-md">{igError}</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-3 gap-4">
                        {mediaList.map((media) => (
                            <div key={media.id} onClick={() => { setSelectedMedia(media); setAiCaption(''); }} className={`relative aspect-square rounded-xl overflow-hidden cursor-pointer border-4 transition-all ${selectedMedia?.id === media.id ? 'border-purple-500 scale-95' : 'border-transparent hover:scale-105'}`}>
                                <img src={media.media_type === 'VIDEO' ? media.thumbnail_url : media.media_url} alt="Post" className="w-full h-full object-cover" />
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Editor IA */}
            <div className="w-1/3 flex flex-col gap-4">
                <div className="bg-white rounded-[2rem] p-6 shadow-sm border border-gray-200 flex-1 flex flex-col">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2"><Wand2 className="text-purple-600"/> Otimizador IA</h3>
                    
                    {selectedMedia ? (
                        <>
                            <div className="mb-4">
                                <label className="text-xs font-black uppercase text-gray-400">Legenda Original</label>
                                <p className="text-xs text-gray-500 bg-gray-50 p-3 rounded-xl mt-1 line-clamp-3 italic">"{selectedMedia.caption || 'Sem legenda'}"</p>
                            </div>

                            <button 
                                onClick={generateAiCopy} 
                                disabled={isGenerating}
                                className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-bold text-sm shadow-lg shadow-purple-200 flex items-center justify-center gap-2 hover:opacity-90 transition-all"
                            >
                                {isGenerating ? <Loader2 className="animate-spin" /> : <><Wand2 size={16}/> Gerar Copy Vendedora</>}
                            </button>

                            <div className="mt-6 flex-1 flex flex-col">
                                <label className="text-xs font-black uppercase text-gray-400 mb-1">Sugestão da IA</label>
                                <textarea 
                                    className="flex-1 w-full bg-purple-50 border border-purple-100 rounded-xl p-4 text-sm text-gray-700 outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                                    placeholder="A mágica aparecerá aqui..."
                                    value={aiCaption}
                                    onChange={(e) => setAiCaption(e.target.value)}
                                />
                                <button className="mt-2 text-purple-600 text-xs font-bold flex items-center gap-1 self-end hover:bg-purple-50 p-2 rounded-lg" onClick={() => navigator.clipboard.writeText(aiCaption)}>
                                    <Copy size={12}/> Copiar Texto
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-center text-gray-400 text-sm px-8">
                            Selecione uma imagem ao lado para começar a mágica.
                        </div>
                    )}
                </div>
            </div>
        </div>
      )}
      
      {/* MODAL NOVO LEAD (MANTIDO) */}
      {isModalOpen && (
          <div className="fixed inset-0 z-[100] bg-slate-900/60 flex items-center justify-center backdrop-blur-sm p-4">
              <div className="bg-white p-8 rounded-[2.5rem] shadow-2xl w-full max-w-md animate-in fade-in zoom-in duration-200 border border-white">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-black text-gray-800">Novo Potencial Paciente</h3>
                      <button onClick={() => setIsModalOpen(false)}><X size={20} className="text-gray-400" /></button>
                  </div>
                  <form onSubmit={handleCreateLead} className="flex flex-col gap-4">
                      <div className="space-y-1">
                        <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Nome Completo</label>
                        <input required className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all" value={newLead.name} onChange={e => setNewLead({...newLead, name: e.target.value})} />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-black uppercase text-gray-400 ml-1">WhatsApp</label>
                        <input className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all" placeholder="55..." value={newLead.phone} onChange={e => setNewLead({...newLead, phone: e.target.value})} />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Origem</label>
                        <select className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all" value={newLead.source} onChange={e => setNewLead({...newLead, source: e.target.value})}>
                            <option value="Manual">Manual (Balcão/Telefone)</option>
                            <option value="Indicação">Indicação</option>
                        </select>
                      </div>
                      <button type="submit" className="w-full bg-blue-600 text-white py-4 rounded-2xl font-black text-sm uppercase tracking-widest mt-4 shadow-lg shadow-blue-100 hover:bg-blue-700 transition-all">Salvar Lead</button>
                  </form>
              </div>
          </div>
      )}
    </div>
  );
}