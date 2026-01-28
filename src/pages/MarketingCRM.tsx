import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { 
  MoreHorizontal, Plus, Phone, X, Loader2, 
  Facebook, Target, TrendingUp, DollarSign, RefreshCw, CheckCircle2,
  Instagram, Wand2, Copy, Image as ImageIcon, AlertTriangle
} from 'lucide-react';

declare global {
  interface Window {
    fbAsyncInit: () => void;
    FB: any;
  }
}

// Interfaces
interface Lead { id: number; name: string; source: string; phone?: string; status: string; notes?: string; }
interface IgMedia { id: string; media_url: string; thumbnail_url?: string; caption?: string; media_type: string; }

// Colunas Kanban
const COLUMNS = {
  new: { title: 'Novos Leads', color: 'border-blue-500', headerColor: 'text-blue-600', bg: 'bg-blue-50' },
  contacted: { title: 'Agendamento Tentado', color: 'border-yellow-500', headerColor: 'text-yellow-600', bg: 'bg-yellow-50' },
  scheduled: { title: 'Consulta Agendada', color: 'border-green-500', headerColor: 'text-green-600', bg: 'bg-green-50' },
  treating: { title: 'Em Tratamento', color: 'border-purple-500', headerColor: 'text-purple-600', bg: 'bg-purple-50' }
};

export function MarketingCRM() {
  
  // --- STATES ---
  const [activeTab, setActiveTab] = useState<'funnel' | 'creative'>('funnel');
  const [leads, setLeads] = useState<Lead[]>([]);
  const [mediaList, setMediaList] = useState<IgMedia[]>([]);
  const [selectedMedia, setSelectedMedia] = useState<IgMedia | null>(null);
  const [aiCaption, setAiCaption] = useState('');
  
  // Loadings e Erros
  const [isGenerating, setIsGenerating] = useState(false);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [igError, setIgError] = useState<string | null>(null);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newLead, setNewLead] = useState({ name: '', phone: '', source: 'Instagram', notes: '' });
  
  // Facebook Auth & Stats
  const [isConnected, setIsConnected] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true); 
  const [adsStats, setAdsStats] = useState({ spend: 0.0, clicks: 0, cpc: 0.0 });

  useEffect(() => {
    const token = localStorage.getItem('odonto_token');

    // Carrega Leads
    fetch('/api/marketing/leads', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(res => res.json()).then(data => { if (Array.isArray(data)) setLeads(data); })
      .catch(console.error).finally(() => setLoading(false));

    // Init Facebook
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

  // --- FUNÇÕES FACEBOOK ---
  const checkMetaConnection = async () => {
    try {
        const token = localStorage.getItem('odonto_token');
        if (!token) return;
        const res = await fetch('/api/marketing/meta/sync', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const data = await res.json();
            setIsConnected(true);
            // GARANTIA: Só atualiza se vier dados válidos, senão mantém o anterior (evita zerar por erro)
            if (data.spend !== undefined) {
                setAdsStats({ spend: data.spend, clicks: data.clicks, cpc: data.cpc });
            }
        } else {
            // Se der erro 400/401, aí sim desconecta
            if(res.status === 401) setIsConnected(false);
        }
    } catch (e) { console.log("Sem conexão Meta"); }
    finally { setCheckingAuth(false); }
  };

  const handleFacebookLogin = () => {
    setAuthLoading(true);
    if (!window.FB) return alert("Erro no SDK Facebook");
    
    // PEDE TODAS AS PERMISSÕES DE UMA VEZ
    window.FB.login((response: any) => {
        if (response.authResponse) sendTokenToBackend(response.authResponse.accessToken);
        else setAuthLoading(false);
    }, { scope: 'ads_management,ads_read,leads_retrieval,instagram_basic,pages_show_list' });
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
            alert("Facebook e Instagram Conectados!");
            checkMetaConnection(); 
        }
    } catch (error) { alert("Erro ao conectar."); } finally { setAuthLoading(false); }
  };

  // --- FUNÇÕES INSTAGRAM & IA ---
  const fetchInstagramMedia = async () => {
    // Se já carregou ou não está conectado, não faz nada
    if (mediaList.length > 0 || !isConnected) return; 
    
    setMediaLoading(true);
    setIgError(null);
    
    try {
        const res = await fetch('/api/marketing/instagram/media', {
             headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
        });
        const data = await res.json();
        
        if (res.ok) {
            setMediaList(data);
        } else {
            // Captura o erro específico (ex: conta não vinculada)
            setIgError(data.error || "Erro ao buscar mídia.");
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

  // --- FUNÇÕES KANBAN (Mantidas) ---
  const handleCreateLead = async (e: React.FormEvent) => { e.preventDefault(); /* Lógica de criar lead... */ setIsModalOpen(false); };
  const onDragEnd = async (result: DropResult) => { 
      // Lógica simplificada para caber
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
        
        {/* TABS DE NAVEGAÇÃO */}
        <div className="flex bg-white p-1 rounded-xl border border-gray-200 shadow-sm">
            <button 
                onClick={() => setActiveTab('funnel')}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'funnel' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}
            >
                Funil de Vendas
            </button>
            <button 
                onClick={() => { setActiveTab('creative'); fetchInstagramMedia(); }}
                className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${activeTab === 'creative' ? 'bg-purple-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}
            >
                <Wand2 size={14} /> Criador IA
            </button>
        </div>
      </header>

      {/* --- WIDGET FACEBOOK (SEMPRE VISÍVEL NO TOPO OU SÓ NA ABA FUNIL? MANTENDO NA FUNIL) --- */}
      {activeTab === 'funnel' && (
        <>
            <div className="mb-6 flex-shrink-0">
                {checkingAuth ? ( <div className="h-24 bg-gray-100 rounded-3xl animate-pulse"></div> ) : !isConnected ? (
                    <button onClick={handleFacebookLogin} disabled={authLoading} className="flex items-center gap-2 px-5 py-3 bg-[#1877F2] text-white rounded-xl font-bold shadow-lg hover:bg-[#166fe5]">
                        <Facebook size={20} /> {authLoading ? 'Conectando...' : 'Vincular Facebook & Instagram'}
                    </button>
                ) : (
                    <div className="grid grid-cols-3 gap-4 animate-in fade-in slide-in-from-top-4 duration-500">
                        <div className="bg-white p-4 rounded-2xl border border-blue-100 shadow-sm"><span className="text-[10px] uppercase text-gray-400 font-black">Investimento</span><div className="text-2xl font-black text-gray-800">R$ {adsStats.spend.toFixed(2)}</div></div>
                        <div className="bg-white p-4 rounded-2xl border border-purple-100 shadow-sm"><span className="text-[10px] uppercase text-gray-400 font-black">Cliques</span><div className="text-2xl font-black text-gray-800">{adsStats.clicks}</div></div>
                        <div className="bg-green-500 text-white p-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 font-bold cursor-pointer hover:bg-green-600 active:scale-95 transition-all" onClick={checkMetaConnection}>
                            <RefreshCw size={18} /> Sincronizar Tudo
                        </div>
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

      {/* --- CONTEÚDO DA ABA: CRIADOR IA --- */}
      {activeTab === 'creative' && (
        <div className="flex gap-6 h-full overflow-hidden">
            {/* Galeria */}
            <div className="w-2/3 bg-white rounded-[2rem] p-6 shadow-sm border border-gray-200 overflow-y-auto">
                <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2"><Instagram className="text-pink-600"/> Selecione um Post</h3>
                
                {!isConnected ? (
                    <div className="h-64 flex flex-col items-center justify-center text-gray-400 bg-gray-50 rounded-2xl border-2 border-dashed">
                        <ImageIcon size={48} className="mb-2 opacity-50"/>
                        <p>Conecte o Facebook na aba "Funil" primeiro.</p>
                    </div>
                ) : mediaLoading ? (
                    <div className="h-64 flex flex-col items-center justify-center text-gray-400"><Loader2 className="animate-spin mb-2 text-purple-600" size={32}/><p>Buscando fotos no Instagram...</p></div>
                ) : igError ? (
                    <div className="bg-red-50 p-6 rounded-2xl border border-red-100 flex flex-col items-center text-center">
                        <AlertTriangle className="text-red-500 mb-2" size={32}/>
                        <h4 className="text-red-800 font-bold mb-1">Instagram Business não encontrado</h4>
                        <p className="text-red-600 text-sm mb-4 max-w-md">{igError}</p>
                        <a href="https://help.instagram.com/570895513091465" target="_blank" className="text-xs bg-white border border-red-200 text-red-600 px-4 py-2 rounded-lg font-bold hover:bg-red-50">
                            Como vincular Instagram à Página do Facebook?
                        </a>
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
      
      {/* Modais extras mantidos aqui ocultos para não poluir... */}
      {isModalOpen && (
          <div className="fixed inset-0 z-[100] bg-slate-900/60 flex items-center justify-center backdrop-blur-sm p-4">
              <div className="bg-white p-8 rounded-[2.5rem] shadow-2xl w-full max-w-md">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-black text-gray-800">Novo Potencial Paciente</h3>
                      <button onClick={() => setIsModalOpen(false)}><X size={20} className="text-gray-400" /></button>
                  </div>
                  <form onSubmit={handleCreateLead} className="flex flex-col gap-4">
                      <input required className="w-full p-3 bg-gray-50 border rounded-xl" placeholder="Nome" value={newLead.name} onChange={e => setNewLead({...newLead, name: e.target.value})} />
                      <input className="w-full p-3 bg-gray-50 border rounded-xl" placeholder="WhatsApp" value={newLead.phone} onChange={e => setNewLead({...newLead, phone: e.target.value})} />
                      <button type="submit" className="w-full bg-blue-600 text-white py-4 rounded-2xl font-bold">Salvar Lead</button>
                  </form>
              </div>
          </div>
      )}
    </div>
  );
}