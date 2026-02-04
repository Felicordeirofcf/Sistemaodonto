import { useState, useEffect, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { 
  Plus, X, Loader2, 
  Facebook, Target, RefreshCw, 
  Instagram, Wand2, Copy, Image as ImageIcon, 
  AlertTriangle, LogOut, FileText, CheckCircle2, Trash2
} from 'lucide-react';

declare global {
  interface Window {
    fbAsyncInit: () => void;
    FB: any;
  }
}

// Interfaces
interface Lead { id: number; name: string; source: string; phone?: string; status: string; notes?: string; }
interface IgMedia { id: string; media_url: string; thumbnail_url?: string; caption?: string; media_type: string; permalink?: string; }
type MetaPage = { id: string; name: string };

const COLUMNS = {
  new: { title: 'Novos Leads', color: 'border-blue-500', headerColor: 'text-blue-600', bg: 'bg-blue-50' },
  contacted: { title: 'Agendamento Tentado', color: 'border-yellow-500', headerColor: 'text-yellow-600', bg: 'bg-yellow-50' },
  scheduled: { title: 'Consulta Agendada', color: 'border-green-500', headerColor: 'text-green-600', bg: 'bg-green-50' },
  treating: { title: 'Em Tratamento', color: 'border-purple-500', headerColor: 'text-purple-600', bg: 'bg-purple-50' }
};

export function MarketingCRM() {
  
  // --- STATES ---
  const [activeTab, setActiveTab] = useState<'funnel' | 'creative'>('funnel');
  const [mediaSource, setMediaSource] = useState<'instagram' | 'facebook'>('instagram');
  const [leads, setLeads] = useState<Lead[]>([]);
  const [mediaList, setMediaList] = useState<IgMedia[]>([]);
  const [selectedMedia, setSelectedMedia] = useState<IgMedia | null>(null);
  const [aiCaption, setAiCaption] = useState('');
  
  // Controls
  const [isGenerating, setIsGenerating] = useState(false);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [igError, setIgError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newLead, setNewLead] = useState({ name: '', phone: '', source: 'Manual', notes: '' });
  
  // Auth
  const [isConnected, setIsConnected] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true); 
  const [adsStats, setAdsStats] = useState({ spend: 0.0, clicks: 0, cpc: 0.0 });

  // Pages Selection
  const [metaPages, setMetaPages] = useState<MetaPage[]>([]);
  const [pagesLoading, setPagesLoading] = useState(false);
  const [selectedPageId, setSelectedPageId] = useState<string>('');
  const [pageSelectedOk, setPageSelectedOk] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  const getHeaders = () => ({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
  });

  // --- INITIALIZATION ---
  useEffect(() => {
    fetch('/api/marketing/leads', { headers: getHeaders() })
      .then(res => res.json()).then(data => { if (Array.isArray(data)) setLeads(data); })
      .catch(console.error).finally(() => setLoading(false));

    window.fbAsyncInit = function() {
        window.FB.init({ 
          appId      : '1566054111352118', // YOUR NEW APP ID
          cookie     : true,
          xfbml      : true,
          version    : 'v19.0'
        });
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

  const checkMetaConnection = useCallback(async () => {
    try {
        const res = await fetch('/api/marketing/meta/sync', { method: 'POST', headers: getHeaders() });
        if (res.ok) {
            const data = await res.json();
            setIsConnected(true);
            if (data.spend !== undefined) setAdsStats({ spend: data.spend, clicks: data.clicks, cpc: data.cpc });
            
            // Check if page is already selected
            if (typeof data.page_selected === 'boolean') setPageSelectedOk(data.page_selected);
            
            fetchMetaPages();
        } else if (res.status === 401) {
            setIsConnected(false);
        }
    } catch (e) { console.log("Meta sync error"); }
    finally { setCheckingAuth(false); }
  }, []);

  const fetchMetaPages = async () => {
      setPagesLoading(true);
      try {
          const res = await fetch('/api/marketing/meta/pages', { headers: getHeaders() });
          const data = await res.json();
          
          if (res.ok && data.pages) {
              setMetaPages(data.pages);
              if(data.current_page_id) setSelectedPageId(data.current_page_id);
              
              if(data.pages.length === 0) {
                  setPageError("Nenhuma Página encontrada. Verifique se você é Administrador da Página no Facebook.");
              }
          } else {
              setPageError("Erro ao listar páginas.");
          }
      } catch (e) { setPageError("Falha na conexão."); }
      finally { setPagesLoading(false); }
  };

  const selectMetaPage = async () => {
      if(!selectedPageId) return;
      setPagesLoading(true);
      try {
          const res = await fetch('/api/marketing/meta/select-page', {
              method: 'POST',
              headers: getHeaders(),
              body: JSON.stringify({ page_id: selectedPageId })
          });
          if (res.ok) {
              setPageSelectedOk(true);
              setPageError(null);
              alert("✅ Página confirmada!");
          } else {
              setPageSelectedOk(false);
              setPageError("Erro ao salvar página.");
          }
      } catch (e) { setPageError("Erro de rede."); }
      finally { setPagesLoading(false); }
  };

  const handleFacebookLogin = () => {
    setAuthLoading(true);
    if (!window.FB) return alert("Erro: Facebook SDK bloqueado.");
    
    // Critical Permissions
    const permissions = 'public_profile,email,pages_show_list,ads_management,ads_read,leads_retrieval,instagram_basic,pages_read_engagement';

    window.FB.login((response: any) => {
        if (response.authResponse) {
            // Check if all permissions were granted
            window.FB.api('/me/permissions', (permResponse: any) => {
                const granted = permResponse.data.filter((p: any) => p.status === 'granted').map((p: any) => p.permission);
                const missing = ['pages_show_list', 'instagram_basic'].filter(p => !granted.includes(p));
                
                if (missing.length > 0) {
                    alert(`⚠️ Atenção: Você não aceitou todas as permissões (${missing.join(', ')}). O sistema não funcionará. Tente novamente e marque todas as caixas.`);
                    setAuthLoading(false);
                } else {
                    sendTokenToBackend(response.authResponse.accessToken);
                }
            });
        } else {
            setAuthLoading(false);
        }
    }, { scope: permissions, auth_type: 'rerequest', return_scopes: true });
  };

  const sendTokenToBackend = async (fbToken: string) => {
    try {
        const res = await fetch('/api/marketing/meta/connect', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ accessToken: fbToken })
        });
        if (res.ok) { 
            setIsConnected(true); 
            alert("Conectado! Agora selecione a Página abaixo.");
            checkMetaConnection(); 
        } else {
            alert("Erro no backend ao salvar token.");
        }
    } catch (error) { alert("Erro de rede."); } 
    finally { setAuthLoading(false); }
  };

  const handleDisconnect = async () => {
    if (!window.confirm("Desconectar conta?")) return;
    setAuthLoading(true);
    try {
        await fetch('/api/marketing/meta/disconnect', { method: 'POST', headers: getHeaders() });
        setIsConnected(false);
        setAdsStats({ spend: 0.0, clicks: 0, cpc: 0.0 });
        setMetaPages([]);
        setPageSelectedOk(false);
        setMediaList([]);
        alert("Desconectado.");
    } catch (e) { alert("Erro."); }
    finally { setAuthLoading(false); }
  };

  const fetchMedia = async (source: 'instagram' | 'facebook') => {
    if (!isConnected) return alert("Conecte sua conta primeiro!");
    if (!pageSelectedOk) return setIgError("⚠️ Selecione e CONFIRME uma Página na aba Funil primeiro.");
    
    setMediaLoading(true);
    setIgError(null);
    setMediaSource(source);
    
    try {
        const endpoint = source === 'instagram' ? '/api/marketing/instagram/media' : '/api/marketing/facebook/media';
        const res = await fetch(endpoint, { headers: getHeaders() });
        const data = await res.json();
        
        if (res.ok) {
            setMediaList(Array.isArray(data) ? data : []);
            if (Array.isArray(data) && data.length === 0) setIgError(`Nenhum post encontrado no ${source}.`);
        } else {
            setIgError(data.error || "Erro ao buscar mídia.");
            setMediaList([]);
        }
    } catch (e) { setIgError("Falha na conexão."); }
    finally { setMediaLoading(false); }
  };

  const generateAiCopy = async () => {
    if (!selectedMedia) return;
    setIsGenerating(true);
    try {
        const res = await fetch('/api/marketing/ai/generate', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ caption: selectedMedia.caption })
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
            headers: getHeaders(),
            body: JSON.stringify({ ...newLead, status: 'new' })
        });
        const saved = await res.json();
        setLeads([...leads, saved]);
        setIsModalOpen(false);
        setNewLead({ name: '', phone: '', source: 'Manual', notes: '' });
      } catch(e) { alert("Erro ao criar lead."); }
  };

  const handleDeleteLead = async (id: number) => {
    if (!window.confirm("Tem certeza que deseja excluir este lead?")) return;
    try {
      const res = await fetch(`/api/marketing/leads/${id}`, {
        method: 'DELETE',
        headers: getHeaders()
      });
      if (res.ok) {
        setLeads(prev => prev.filter(l => l.id !== id));
      } else {
        alert("Erro ao excluir lead.");
      }
    } catch (e) {
      alert("Erro de rede ao excluir lead.");
    }
  };

  const onDragEnd = async (result: DropResult) => { 
      if (!result.destination) return;
      const newStatus = result.destination.droppableId;
      const leadId = parseInt(result.draggableId);
      const oldLeads = [...leads];
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));
      try { await fetch(`/api/marketing/leads/${leadId}/move`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ status: newStatus }) }); } catch (e) { setLeads(oldLeads); }
  };
  
  const getColumnLeads = (status: string) => leads.filter(l => l.status === status);

  return (
    <div className="p-8 w-full h-screen overflow-hidden flex flex-col bg-gray-50 relative font-sans">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-6 flex-shrink-0">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Marketing & Ads</h1>
          <p className="text-gray-500 font-medium">Automação de Leads e Criativos com IA.</p>
        </div>
        <div className="flex items-center gap-4">
            <div className="flex bg-white p-1 rounded-xl border border-gray-200 shadow-sm">
                <button onClick={() => setActiveTab('funnel')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'funnel' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}>Funil</button>
                <button onClick={() => { setActiveTab('creative'); if(isConnected) fetchMedia('instagram'); }} className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${activeTab === 'creative' ? 'bg-purple-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}><Wand2 size={14} /> IA</button>
            </div>
            <button onClick={() => setIsModalOpen(true)} className="px-6 py-3 bg-gray-900 text-white rounded-xl font-bold text-sm hover:bg-gray-800 flex items-center gap-2 shadow-xl active:scale-95"><Plus size={18} /> Lead</button>
        </div>
      </header>

      {activeTab === 'funnel' && (
        <>
            <div className="mb-6 flex-shrink-0">
                {checkingAuth ? ( <div className="h-24 bg-gray-100 rounded-3xl animate-pulse"></div> ) : !isConnected ? (
                    <div className="bg-white p-6 rounded-3xl border border-blue-100 shadow-sm flex items-center justify-between animate-in zoom-in">
                        <div className="flex items-center gap-4">
                            <div className="bg-blue-50 p-3 rounded-2xl text-blue-600"><Target size={32}/></div>
                            <div>
                                <h3 className="font-bold text-gray-800 text-lg">Conectar Redes Sociais</h3>
                                <p className="text-gray-500 text-xs mt-1">Vincule sua conta Meta para importar dados.</p>
                            </div>
                        </div>
                        <button onClick={handleFacebookLogin} disabled={authLoading} className="flex items-center gap-2 px-6 py-3 bg-[#1877F2] text-white rounded-xl font-bold shadow-lg hover:bg-[#166fe5] active:scale-95">
                            <Facebook size={20} /> {authLoading ? 'Conectando...' : 'Conectar Agora'}
                        </button>
                    </div>
                ) : (
                    <div className="flex flex-col gap-4 animate-in slide-in-from-top-4">
                        <div className="flex justify-between items-start gap-4">
                            <div className="grid grid-cols-3 gap-4 flex-1">
                                <div className="bg-white p-4 rounded-2xl border border-blue-100 shadow-sm"><span className="text-[10px] uppercase text-gray-400 font-black">Investimento</span><div className="text-2xl font-black text-gray-800">R$ {adsStats.spend.toFixed(2)}</div></div>
                                <div className="bg-white p-4 rounded-2xl border border-purple-100 shadow-sm"><span className="text-[10px] uppercase text-gray-400 font-black">Cliques</span><div className="text-2xl font-black text-gray-800">{adsStats.clicks}</div></div>
                                <div className="bg-green-500 text-white p-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 font-bold cursor-pointer hover:bg-green-600 active:scale-95 transition-all" onClick={checkMetaConnection}><RefreshCw size={18} /> Sincronizar</div>
                            </div>
                            <button onClick={handleDisconnect} disabled={authLoading} className="bg-red-50 text-red-600 border border-red-200 p-4 rounded-2xl shadow-sm flex items-center justify-center gap-2 font-bold cursor-pointer hover:bg-red-100 active:scale-95 h-full"><LogOut size={18} /></button>
                        </div>

                        {/* SELECT DE PÁGINAS */}
                        <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm flex flex-col gap-3">
                            <div className="flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    <div className={`p-3 rounded-2xl ${pageSelectedOk ? 'bg-green-50 text-green-600' : 'bg-purple-50 text-purple-700'}`}><CheckCircle2 size={22} /></div>
                                    <div><h4 className="font-black text-gray-800">Selecione a Página do Facebook</h4><p className="text-xs text-gray-500 font-medium">Obrigatório para buscar posts.</p></div>
                                </div>
                                <button onClick={fetchMetaPages} disabled={pagesLoading} className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 font-bold text-xs hover:bg-gray-200 active:scale-95 flex items-center gap-2">{pagesLoading ? <Loader2 className="animate-spin" size={14}/> : <RefreshCw size={14}/>} Atualizar lista</button>
                            </div>
                            {pageError && <div className="bg-red-50 border border-red-100 text-red-700 p-4 rounded-2xl text-sm flex items-start gap-3"><AlertTriangle className="mt-0.5" size={18}/><div><div className="font-black">Atenção</div><div className="text-xs font-medium">{pageError}</div></div></div>}
                            <div className="flex flex-col md:flex-row gap-3">
                                <select className="flex-1 w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-purple-500 transition-all text-sm font-bold text-gray-700" value={selectedPageId} onChange={(e) => { setSelectedPageId(e.target.value); setPageSelectedOk(false); }} disabled={pagesLoading || !metaPages.length}>
                                    <option value="">{metaPages.length ? '-- Selecione uma Página --' : (pagesLoading ? 'Carregando...' : 'Nenhuma página encontrada')}</option>
                                    {metaPages.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                </select>
                                <button onClick={selectMetaPage} disabled={!selectedPageId || pagesLoading} className={`px-5 py-3 rounded-xl font-black text-sm transition-all active:scale-95 flex items-center justify-center gap-2 ${selectedPageId && !pagesLoading ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-lg shadow-purple-200' : 'bg-gray-200 text-gray-500 cursor-not-allowed'}`}>{pagesLoading ? <Loader2 className="animate-spin" size={18}/> : <CheckCircle2 size={18}/>} Confirmar</button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
            
            <DragDropContext onDragEnd={onDragEnd}>
                <div className="flex-1 overflow-x-auto pb-4"><div className="flex gap-6 h-full min-w-[1200px]">
                    {Object.entries(COLUMNS).map(([id, cfg]) => (
                        <div key={id} className="flex flex-col bg-gray-200/30 rounded-[2rem] w-80 h-full border border-gray-200/50">
                            <div className={`bg-white p-4 rounded-t-[2rem] border-t-8 ${cfg.color} font-black text-xs uppercase ${cfg.headerColor} flex justify-between`}><span>{cfg.title}</span><span className="bg-gray-100 px-2 rounded text-gray-500 text-[10px]">{getColumnLeads(id).length}</span></div>
                            <Droppable droppableId={id}>{(p, s) => (<div {...p.droppableProps} ref={p.innerRef} className="flex-1 p-4 flex flex-col gap-3 overflow-y-auto">{getColumnLeads(id).map((item, idx) => (
                                <Draggable key={item.id} draggableId={String(item.id)} index={idx}>{(p, s) => (
                                    <div ref={p.innerRef} {...p.draggableProps} {...p.dragHandleProps} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 group hover:border-blue-300 transition-all relative">
                                        <button 
                                          onClick={() => handleDeleteLead(item.id)}
                                          className="absolute top-2 right-2 p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                          title="Excluir Lead"
                                        >
                                          <Trash2 size={14} />
                                        </button>
                                        <div className="font-bold text-sm text-gray-800 pr-6">{item.name}</div>
                                        <div className="flex items-center gap-1 text-[10px] text-gray-400 mt-2 uppercase font-bold"><div className={`w-1.5 h-1.5 rounded-full ${item.source === 'Instagram' ? 'bg-purple-500' : item.source === 'Facebook' ? 'bg-blue-600' : 'bg-gray-400'}`}></div>{item.source}</div>
                                    </div>
                                )}</Draggable>
                            ))}{p.placeholder}</div>)}</Droppable>
                        </div>
                    ))}
                </div></div>
            </DragDropContext>
        </>
      )}

      {/* --- ABA CREATIVE --- */}
      {activeTab === 'creative' && (
        <div className="flex gap-6 h-full overflow-hidden">
            <div className="w-2/3 bg-white rounded-[2rem] p-6 shadow-sm border border-gray-200 overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">{mediaSource === 'instagram' ? <Instagram className="text-pink-600"/> : <Facebook className="text-blue-600"/>} Selecione um Post</h3>
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        <button onClick={() => fetchMedia('instagram')} className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${mediaSource === 'instagram' ? 'bg-white shadow text-pink-600' : 'text-gray-500 hover:text-gray-700'}`}>Instagram</button>
                        <button onClick={() => fetchMedia('facebook')} className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${mediaSource === 'facebook' ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>Facebook</button>
                    </div>
                </div>
                {!isConnected ? <div className="h-64 flex flex-col items-center justify-center text-gray-400 bg-gray-50 rounded-2xl border-2 border-dashed"><ImageIcon size={48} className="mb-2 opacity-50"/><p>Conecte as Redes Sociais na aba "Funil" primeiro.</p></div> 
                : !pageSelectedOk ? <div className="bg-yellow-50 p-6 rounded-2xl border border-yellow-100 flex flex-col items-center text-center"><AlertTriangle className="text-yellow-600 mb-2" size={32}/><h4 className="text-yellow-900 font-bold mb-1">Selecione uma Página</h4><p className="text-yellow-800 text-sm">Vá na aba <b>Funil</b> e selecione uma Página do Facebook.</p></div>
                : mediaLoading ? <div className="h-64 flex flex-col items-center justify-center text-gray-400"><Loader2 className="animate-spin mb-2 text-purple-600" size={32}/><p>Buscando posts...</p></div>
                : igError ? <div className="bg-red-50 p-6 rounded-2xl border border-red-100 flex flex-col items-center text-center"><AlertTriangle className="text-red-500 mb-2" size={32}/><h4 className="text-red-800 font-bold mb-1">Atenção</h4><p className="text-red-600 text-sm mb-4 max-w-md">{igError}</p></div>
                : <div className="grid grid-cols-3 gap-4">{mediaList.map((media) => (<div key={media.id} onClick={() => { setSelectedMedia(media); setAiCaption(''); }} className={`relative aspect-square rounded-xl overflow-hidden cursor-pointer border-4 transition-all ${selectedMedia?.id === media.id ? 'border-purple-500 scale-95' : 'border-transparent hover:scale-105'}`}><img src={media.media_type === 'VIDEO' ? media.thumbnail_url : media.media_url} alt="Post" className="w-full h-full object-cover" /></div>))}</div>}
            </div>

            <div className="w-1/3 flex flex-col gap-4">
                <div className="bg-white rounded-[2rem] p-6 shadow-sm border border-gray-200 flex-1 flex flex-col">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2"><Wand2 className="text-purple-600"/> Otimizador IA</h3>
                    {selectedMedia ? (
                        <>
                            <div className="mb-4"><label className="text-xs font-black uppercase text-gray-400">Legenda Original</label><div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-xl mt-1 max-h-24 overflow-y-auto italic">"{selectedMedia.caption || 'Post sem legenda'}"</div></div>
                            <button onClick={generateAiCopy} disabled={isGenerating} className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-bold text-sm shadow-lg shadow-purple-200 flex items-center justify-center gap-2 hover:opacity-90 transition-all">{isGenerating ? <Loader2 className="animate-spin" /> : <><Wand2 size={16}/> Gerar Copy Vendedora</>}</button>
                            <div className="mt-6 flex-1 flex flex-col"><label className="text-xs font-black uppercase text-gray-400 mb-1">Sugestão da IA</label><textarea className="flex-1 w-full bg-purple-50 border border-purple-100 rounded-xl p-4 text-sm text-gray-700 outline-none focus:ring-2 focus:ring-purple-500 resize-none" placeholder="A mágica aparecerá aqui..." value={aiCaption} onChange={(e) => setAiCaption(e.target.value)} /><button className="mt-2 text-purple-600 text-xs font-bold flex items-center gap-1 self-end hover:bg-purple-50 p-2 rounded-lg" onClick={() => navigator.clipboard.writeText(aiCaption)} disabled={!aiCaption}><Copy size={12}/> Copiar Texto</button></div>
                        </>
                    ) : <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400 text-sm px-8 gap-4"><FileText size={48} className="opacity-20"/><p>Selecione uma imagem ao lado para a Inteligência Artificial criar uma legenda de alta conversão.</p></div>}
                </div>
            </div>
        </div>
      )}
      
      {isModalOpen && (
          <div className="fixed inset-0 z-[100] bg-slate-900/60 flex items-center justify-center backdrop-blur-sm p-4">
              <div className="bg-white p-8 rounded-[2.5rem] shadow-2xl w-full max-w-md animate-in fade-in zoom-in duration-200 border border-white">
                  <div className="flex justify-between items-center mb-6">
                      <h2 className="text-2xl font-black text-gray-900">Novo Lead</h2>
                      <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors"><X size={24} /></button>
                  </div>
                  <form onSubmit={handleCreateLead} className="space-y-4">
                      <div><label className="block text-xs font-black text-gray-400 uppercase mb-1">Nome Completo</label><input type="text" required className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 transition-all font-bold" value={newLead.name} onChange={e => setNewLead({...newLead, name: e.target.value})} /></div>
                      <div><label className="block text-xs font-black text-gray-400 uppercase mb-1">WhatsApp</label><input type="text" required className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 transition-all font-bold" value={newLead.phone} onChange={e => setNewLead({...newLead, phone: e.target.value})} /></div>
                      <div><label className="block text-xs font-black text-gray-400 uppercase mb-1">Origem</label><select className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 transition-all font-bold" value={newLead.source} onChange={e => setNewLead({...newLead, source: e.target.value})}><option>Manual</option><option>Instagram</option><option>Facebook</option><option>Google</option></select></div>
                      <button type="submit" className="w-full py-4 bg-gray-900 text-white rounded-2xl font-black shadow-xl hover:bg-gray-800 transition-all active:scale-95 mt-4">Salvar Lead</button>
                  </form>
              </div>
          </div>
      )}
    </div>
  );
}
