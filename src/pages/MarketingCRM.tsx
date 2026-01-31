import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { 
  Plus, X, Loader2, 
  Facebook, Target, RefreshCw, 
  Instagram, Wand2, Copy, Image as ImageIcon, 
  AlertTriangle, LogOut, FileText, CheckCircle2
} from 'lucide-react';

declare global {
  interface Window {
    fbAsyncInit: () => void;
    FB: any;
  }
}

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
  
  // Loadings e Controle
  const [isGenerating, setIsGenerating] = useState(false);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [igError, setIgError] = useState<string | null>(null);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newLead, setNewLead] = useState({ name: '', phone: '', source: 'Manual', notes: '' });
  
  // Facebook Auth
  const [isConnected, setIsConnected] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true); 
  const [adsStats, setAdsStats] = useState({ spend: 0.0, clicks: 0, cpc: 0.0 });

  // Meta Pages (NOVO)
  const [metaPages, setMetaPages] = useState<MetaPage[]>([]);
  const [pagesLoading, setPagesLoading] = useState(false);
  const [selectedPageId, setSelectedPageId] = useState<string>('');
  const [pageSelectedOk, setPageSelectedOk] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);

  const apiAuthHeaders = () => ({
      'Authorization': `Bearer ${localStorage.getItem('odonto_token') || ''}`
  });

  // --- 1. INICIALIZAÇÃO ---
  useEffect(() => {
    const token = localStorage.getItem('odonto_token');
    
    // Busca Leads
    fetch('/api/marketing/leads', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(res => res.json()).then(data => { if (Array.isArray(data)) setLeads(data); })
      .catch(console.error).finally(() => setLoading(false));

    // Inicializa Facebook SDK
    window.fbAsyncInit = function() {
        window.FB.init({ 
          appId      : '1566054111352118', 
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

  // --- FUNÇÕES DE CONEXÃO ---
  const checkMetaConnection = async () => {
    try {
        const token = localStorage.getItem('odonto_token');
        if (!token) return;
        
        const res = await fetch('/api/marketing/meta/sync', { 
            method: 'POST', 
            headers: apiAuthHeaders() 
        });
        
        if (res.ok) {
            const data = await res.json();
            setIsConnected(true);
            
            if (data.spend !== undefined) {
                setAdsStats({ spend: data.spend, clicks: data.clicks, cpc: data.cpc });
            }
            
            // Se backend retorna page_selected (novo)
            if(typeof data.page_selected === 'boolean') {
                setPageSelectedOk(data.page_selected);
            }

            // Atualiza páginas sempre que estiver conectado (pra o usuário escolher)
            await fetchMetaPages();

        } else {
            if(res.status === 401) {
                setIsConnected(false);
                setMetaPages([]);
                setSelectedPageId('');
                setPageSelectedOk(false);
            }
        }
    } catch (e) { console.log("Sem conexão Meta"); }
    finally { setCheckingAuth(false); }
  };

  const handleFacebookLogin = () => {
    setAuthLoading(true);
    
    if (!window.FB) {
        alert("Erro: Facebook SDK bloqueado. Desative o AdBlock.");
        setAuthLoading(false);
        return;
    }
    
    // Permissões mínimas p/ listar páginas e buscar IG/FB
    const permissions = 'public_profile,email,pages_show_list,pages_read_engagement,instagram_basic';

    window.FB.login((response: any) => {
        if (response.authResponse) {
            sendTokenToBackend(response.authResponse.accessToken);
        } else {
            console.log("Login cancelado");
            setAuthLoading(false);
        }
    }, { 
        scope: permissions,
        auth_type: 'rerequest', 
        return_scopes: true 
    });
  };

  const sendTokenToBackend = async (fbToken: string) => {
    try {
        const res = await fetch('/api/marketing/meta/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...apiAuthHeaders() },
            body: JSON.stringify({ accessToken: fbToken })
        });
        
        if (res.ok) { 
            setIsConnected(true); 
            setPageSelectedOk(false);
            setSelectedPageId('');
            setPageError(null);
            
            alert("Conectado! Agora selecione uma Página do Facebook.");
            await checkMetaConnection(); 
        } else {
            const err = await res.json().catch(()=>({}));
            alert("Erro ao conectar: " + (err.error || "Tente novamente"));
        }
    } catch (error) { alert("Erro de rede."); } 
    finally { setAuthLoading(false); }
  };

  const handleDisconnect = async () => {
    if (!window.confirm("Deseja desconectar?")) return;
    setAuthLoading(true);
    try {
        const res = await fetch('/api/marketing/meta/disconnect', {
            method: 'POST',
            headers: apiAuthHeaders()
        });
        
        if (res.ok) {
            setIsConnected(false);
            setAdsStats({ spend: 0.0, clicks: 0, cpc: 0.0 });
            
            // limpa estados de seleção
            setMetaPages([]);
            setSelectedPageId('');
            setPageSelectedOk(false);
            setPageError(null);
            
            setMediaList([]);
            setSelectedMedia(null);
            setAiCaption('');
            alert("Desconectado.");
        }
    } catch (e) { alert("Erro ao desconectar."); }
    finally { setAuthLoading(false); }
  };

  // --- PÁGINAS META (NOVO) ---
  const fetchMetaPages = async () => {
      if(!isConnected) return;
      setPagesLoading(true);
      setPageError(null);
      
      try {
          const res = await fetch('/api/marketing/meta/pages', {
              headers: apiAuthHeaders()
          });
          
          const data = await res.json().catch(()=>({}));
          if(!res.ok || data?.ok === false) {
              setMetaPages([]);
              setPageSelectedOk(false);
              
              // Mensagem mais realista
              setPageError(data?.error || "Não foi possível listar suas páginas. Verifique se sua conta é ADMIN de uma Página no Facebook e se o app está em modo LIVE.");
              return;
          }
          
          const pages = Array.isArray(data.pages) ? data.pages : [];
          setMetaPages(pages);
          
          if(!pages.length) {
              setPageError("Nenhuma Página retornou para sua conta. Você precisa ser ADMIN de uma Página no Facebook (e, para Instagram, o IG precisa estar vinculado a essa Página).");
          }
      } catch (e) {
          setPageError("Falha ao buscar páginas. Verifique sua conexão.");
      } finally {
          setPagesLoading(false);
      }
  };

  const selectMetaPage = async () => {
      if(!selectedPageId) return;
      setPageError(null);
      setPagesLoading(true);
      
      try {
          const res = await fetch('/api/marketing/meta/select-page', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', ...apiAuthHeaders() },
              body: JSON.stringify({ page_id: selectedPageId })
          });
          
          const data = await res.json().catch(()=>({}));
          if(!res.ok || data?.ok === false) {
              setPageSelectedOk(false);
              setPageError(data?.error || "Erro ao selecionar página.");
              return;
          }
          
          setPageSelectedOk(true);
      } catch (e) {
          setPageSelectedOk(false);
          setPageError("Falha ao selecionar página.");
      } finally {
          setPagesLoading(false);
      }
  };

  // --- FUNÇÕES DE MÍDIA E IA ---
  const fetchMedia = async (source: 'instagram' | 'facebook') => {
    if (!isConnected) return alert("Conecte sua conta primeiro na aba Funil!");
    
    // Se não tiver página selecionada, oriente direto
    if (!pageSelectedOk) {
        setIgError("Selecione uma Página do Facebook na aba Funil antes de buscar posts.");
        setMediaList([]);
        return;
    }
    
    setMediaLoading(true);
    setIgError(null);
    setMediaSource(source);
    
    try {
        const endpoint = source === 'instagram' 
            ? '/api/marketing/instagram/media' 
            : '/api/marketing/facebook/media';
            
        const res = await fetch(endpoint, {
             headers: apiAuthHeaders()
        });
        
        const data = await res.json().catch(()=>({}));
        
        if (res.ok) {
            if (Array.isArray(data) && data.length === 0) {
                setIgError(`Nenhum post encontrado no ${source}.`);
                setMediaList([]);
            } else {
                setMediaList(Array.isArray(data) ? data : []);
            }
        } else {
            // 409 = estado inválido (ex.: sem página selecionada / IG não vinculado)
            if(res.status === 409) {
                setIgError(data?.error || "Configuração incompleta. Selecione uma Página e verifique vínculo do Instagram.");
            } else if (res.status === 401) {
                setIgError("Sessão Meta inválida. Desconecte e conecte novamente.");
                setIsConnected(false);
                setPageSelectedOk(false);
            } else {
                setIgError(data?.error || `Erro ao buscar mídia do ${source}.`);
            }
            setMediaList([]);
        }
    } catch (e) { 
        setIgError("Falha na conexão com o servidor."); 
        setMediaList([]);
    }
    finally { setMediaLoading(false); }
  };

  const generateAiCopy = async () => {
    if (!selectedMedia) return;
    setIsGenerating(true);
    try {
        const res = await fetch('/api/marketing/ai/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...apiAuthHeaders() },
            body: JSON.stringify({ caption: selectedMedia.caption, tone: 'persuasive' })
        });
        const data = await res.json();
        setAiCaption(data.suggestion);
    } catch (e) { alert("Erro na IA"); }
    finally { setIsGenerating(false); }
  };

  // --- LEADS MANUAIS ---
  const handleCreateLead = async (e: React.FormEvent) => { 
      e.preventDefault(); 
      try {
        const res = await fetch('/api/marketing/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...apiAuthHeaders() },
            body: JSON.stringify({ ...newLead, status: 'new' })
        });
        const saved = await res.json();
        setLeads([...leads, saved]);
        setIsModalOpen(false);
        setNewLead({ name: '', phone: '', source: 'Manual', notes: '' });
      } catch(e) { alert("Erro ao criar lead manual"); }
  };

  const onDragEnd = async (result: DropResult) => { 
      if (!result.destination) return;
      
      const newStatus = result.destination.droppableId;
      const leadId = parseInt(result.draggableId);
      const oldLeads = [...leads];
      
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));
      
      try { 
          await fetch(`/api/marketing/leads/${leadId}/move`, { 
              method: 'PUT', 
              headers: { 'Content-Type': 'application/json', ...apiAuthHeaders() }, 
              body: JSON.stringify({ status: newStatus }) 
          }); 
      } catch (e) { setLeads(oldLeads); }
  };
  
  const getColumnLeads = (status: string) => leads.filter(l => l.status === status);

  if (loading && !isConnected) return <div className="flex h-screen items-center justify-center bg-gray-50"><Loader2 className="animate-spin text-blue-600" size={48} /></div>;

  return (
    <div className="p-8 w-full h-screen overflow-hidden flex flex-col bg-gray-50 relative font-sans">
      
      {/* HEADER */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-6 flex-shrink-0">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Marketing & Ads</h1>
          <p className="text-gray-500 font-medium">Automação de Leads e Criativos com IA.</p>
        </div>
        
        <div className="flex items-center gap-4">
            <div className="flex bg-white p-1 rounded-xl border border-gray-200 shadow-sm">
                <button 
                    onClick={() => setActiveTab('funnel')}
                    className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'funnel' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}
                >
                    Funil
                </button>
                
                <button 
                    onClick={() => { 
                        setActiveTab('creative'); 
                        if(isConnected) fetchMedia('instagram'); 
                    }}
                    className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${activeTab === 'creative' ? 'bg-purple-600 text-white shadow-md' : 'text-gray-500 hover:bg-gray-50'}`}
                >
                    <Wand2 size={14} /> IA
                </button>
            </div>

            <button onClick={() => setIsModalOpen(true)} className="px-6 py-3 bg-gray-900 text-white rounded-xl font-bold text-sm hover:bg-gray-800 flex items-center gap-2 shadow-xl active:scale-95"><Plus size={18} /> Lead</button>
        </div>
      </header>

      {/* --- ABA FUNIL --- */}
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
                            
                            <button 
                                onClick={handleDisconnect} 
                                disabled={authLoading}
                                className="bg-red-50 text-red-600 border border-red-200 p-4 rounded-2xl shadow-sm flex items-center justify-center gap-2 font-bold cursor-pointer hover:bg-red-100 active:scale-95 h-full"
                            >
                                <LogOut size={18} />
                            </button>
                        </div>

                        {/* SELECT DE PÁGINAS (NOVO) */}
                        <div className="bg-white p-6 rounded-3xl border border-gray-200 shadow-sm flex flex-col gap-3">
                            <div className="flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    <div className="bg-purple-50 p-3 rounded-2xl text-purple-700">
                                        <CheckCircle2 size={22} />
                                    </div>
                                    <div>
                                        <h4 className="font-black text-gray-800">Selecione a Página do Facebook</h4>
                                        <p className="text-xs text-gray-500 font-medium">Sem Página selecionada, não dá pra puxar posts do Facebook nem mídia do Instagram Business.</p>
                                    </div>
                                </div>
                                
                                <button 
                                    onClick={fetchMetaPages} 
                                    disabled={pagesLoading}
                                    className="px-4 py-2 rounded-xl bg-gray-100 text-gray-700 font-bold text-xs hover:bg-gray-200 active:scale-95 flex items-center gap-2"
                                >
                                    {pagesLoading ? <Loader2 className="animate-spin" size={14}/> : <RefreshCw size={14}/>} 
                                    Atualizar páginas
                                </button>
                            </div>

                            {pageError && (
                                <div className="bg-red-50 border border-red-100 text-red-700 p-4 rounded-2xl text-sm flex items-start gap-3">
                                    <AlertTriangle className="mt-0.5" size={18}/>
                                    <div>
                                        <div className="font-black">Atenção</div>
                                        <div className="text-xs font-medium">{pageError}</div>
                                    </div>
                                </div>
                            )}

                            <div className="flex flex-col md:flex-row gap-3">
                                <select 
                                    className="flex-1 w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-purple-500 transition-all text-sm font-bold text-gray-700"
                                    value={selectedPageId}
                                    onChange={(e) => {
                                        setSelectedPageId(e.target.value);
                                        setPageSelectedOk(false); 
                                    }}
                                    disabled={pagesLoading || !metaPages.length}
                                >
                                    <option value="">{metaPages.length ? '-- Selecione uma Página --' : (pagesLoading ? 'Carregando...' : 'Nenhuma página disponível')}</option>
                                    {metaPages.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                                </select>

                                <button 
                                    onClick={selectMetaPage}
                                    disabled={!selectedPageId || pagesLoading}
                                    className={`px-5 py-3 rounded-xl font-black text-sm transition-all active:scale-95 flex items-center justify-center gap-2
                                        ${selectedPageId && !pagesLoading 
                                            ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-lg shadow-purple-200' 
                                            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                        }`}
                                >
                                    {pagesLoading ? <Loader2 className="animate-spin" size={18}/> : <CheckCircle2 size={18}/>}
                                    Confirmar Página
                                </button>
                            </div>

                            <div className="text-xs font-bold">
                                Status: {pageSelectedOk ? <span className="text-green-600">Página selecionada ✅</span> : <span className="text-gray-500">Seleção pendente</span>}
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
                                    <div ref={p.innerRef} {...p.draggableProps} {...p.dragHandleProps} className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 group hover:border-blue-300 transition-all">
                                        <div className="font-bold text-sm text-gray-800">{item.name}</div>
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
                : !pageSelectedOk ? (
                    <div className="bg-yellow-50 p-6 rounded-2xl border border-yellow-100 flex flex-col items-center text-center">
                        <AlertTriangle className="text-yellow-600 mb-2" size={32}/>
                        <h4 className="text-yellow-900 font-bold mb-1">Seleção de Página pendente</h4>
                        <p className="text-yellow-800 text-sm mb-4 max-w-md">Vá na aba <b>Funil</b> e selecione uma Página do Facebook. Sem isso, não dá pra buscar posts do Facebook nem mídia do Instagram Business.</p>
                    </div>
                ) : mediaLoading ? <div className="h-64 flex flex-col items-center justify-center text-gray-400"><Loader2 className="animate-spin mb-2 text-purple-600" size={32}/><p>Buscando posts...</p></div>
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
      
      {/* MODAL NOVO LEAD */}
      {isModalOpen && (
          <div className="fixed inset-0 z-[100] bg-slate-900/60 flex items-center justify-center backdrop-blur-sm p-4">
              <div className="bg-white p-8 rounded-[2.5rem] shadow-2xl w-full max-w-md animate-in fade-in zoom-in duration-200 border border-white">
                  <div className="flex justify-between items-center mb-6"><h3 className="text-xl font-black text-gray-800">Novo Potencial Paciente</h3><button onClick={() => setIsModalOpen(false)}><X size={20} className="text-gray-400" /></button></div>
                  <form onSubmit={handleCreateLead} className="flex flex-col gap-4">
                      <div className="space-y-1"><label className="text-[10px] font-black uppercase text-gray-400 ml-1">Nome Completo</label><input required className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all" value={newLead.name} onChange={e => setNewLead({...newLead, name: e.target.value})} /></div>
                      <div className="space-y-1"><label className="text-[10px] font-black uppercase text-gray-400 ml-1">WhatsApp</label><input className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all" placeholder="55..." value={newLead.phone} onChange={e => setNewLead({...newLead, phone: e.target.value})} /></div>
                      <div className="space-y-1"><label className="text-[10px] font-black uppercase text-gray-400 ml-1">Origem</label><select className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all" value={newLead.source} onChange={e => setNewLead({...newLead, source: e.target.value})}><option value="Manual">Manual (Balcão/Telefone)</option><option value="Indicação">Indicação</option></select></div>
                      <button type="submit" className="w-full bg-blue-600 text-white py-4 rounded-2xl font-black text-sm uppercase tracking-widest mt-4 shadow-lg shadow-blue-100 hover:bg-blue-700 transition-all">Salvar Lead</button>
                  </form>
              </div>
          </div>
      )}
    </div>
  );
}