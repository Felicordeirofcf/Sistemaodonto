import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { 
  MoreHorizontal, Plus, Phone, X, Loader2, 
  Facebook, Target, TrendingUp, DollarSign, RefreshCw 
} from 'lucide-react';

// --- TIPAGEM DO FACEBOOK SDK ---
declare global {
  interface Window {
    fbAsyncInit: () => void;
    FB: any;
  }
}

interface Lead {
  id: number;
  name: string;
  source: string;
  phone?: string;
  status: string;
  notes?: string;
}

const COLUMNS = {
  new: { title: 'Novos Leads', color: 'border-blue-500', headerColor: 'text-blue-600', bg: 'bg-blue-50' },
  contacted: { title: 'Agendamento Tentado', color: 'border-yellow-500', headerColor: 'text-yellow-600', bg: 'bg-yellow-50' },
  scheduled: { title: 'Consulta Agendada', color: 'border-green-500', headerColor: 'text-green-600', bg: 'bg-green-50' },
  treating: { title: 'Em Tratamento', color: 'border-purple-500', headerColor: 'text-purple-600', bg: 'bg-purple-50' }
};

// ✅ CORREÇÃO: Usando "export function" para satisfazer o App.tsx
export function MarketingCRM() {
  
  // --- STATES DO CRM (Kanban) ---
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [newLead, setNewLead] = useState({ name: '', phone: '', source: 'Instagram', notes: '' });

  // --- STATES DA INTEGRAÇÃO FACEBOOK ---
  const [isConnected, setIsConnected] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [adsStats, setAdsStats] = useState({ spend: 0.0, clicks: 0, cpc: 0.0 });

  // --- 1. INICIALIZAÇÃO (FACEBOOK + LEADS) ---
  useEffect(() => {
    // A. Busca Leads do Banco
    fetch('/api/marketing/leads', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
      .then(res => res.json())
      .then(data => { if (Array.isArray(data)) setLeads(data); })
      .catch(console.error)
      .finally(() => setLoading(false));

    // B. Inicializa Facebook SDK
    window.fbAsyncInit = function() {
        window.FB.init({
          appId      : '928590639502117', // ✅ SEU ID JÁ CONFIGURADO AQUI
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

    // C. Checa se já está conectado
    checkMetaConnection();
  }, []);

  // --- LÓGICA DO FACEBOOK ---
  const checkMetaConnection = async () => {
    try {
        const res = await fetch('/api/marketing/meta/sync', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
        });
        if (res.ok) {
            const data = await res.json();
            setIsConnected(true);
            setAdsStats({ 
                spend: data.spend || 0, 
                clicks: data.clicks || 0, 
                cpc: data.cpc || 0 
            });
        }
    } catch (e) { console.log("Meta não conectado"); }
  };

  const handleFacebookLogin = () => {
    setAuthLoading(true);
    if (!window.FB) {
        alert("Erro: Facebook SDK não carregou. Verifique bloqueadores de popup.");
        setAuthLoading(false);
        return;
    }

    window.FB.login((response: any) => {
        if (response.authResponse) {
            sendTokenToBackend(response.authResponse.accessToken);
        } else {
            console.log("Login cancelado");
            setAuthLoading(false);
        }
    }, { scope: 'ads_management,ads_read' });
  };

  const sendTokenToBackend = async (token: string) => {
    try {
        const res = await fetch('/api/marketing/meta/connect', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
            },
            body: JSON.stringify({ accessToken: token })
        });
        if (res.ok) {
            setIsConnected(true);
            alert("✅ Conta vinculada com sucesso!");
            checkMetaConnection();
        } else {
            throw new Error("Falha ao salvar token");
        }
    } catch (error) {
        alert("Erro ao conectar com servidor.");
    } finally {
        setAuthLoading(false);
    }
  };

  // --- LÓGICA DO CRM (KANBAN) ---
  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        const res = await fetch('/api/marketing/leads', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
            },
            body: JSON.stringify({ ...newLead, status: 'new' })
        });
        const savedLead = await res.json();
        setLeads([...leads, savedLead]);
        setIsModalOpen(false);
        setNewLead({ name: '', phone: '', source: 'Instagram', notes: '' });
    } catch (error) { alert("Erro ao criar lead"); }
  };

  const onDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const newStatus = destination.droppableId;
    const leadId = parseInt(draggableId);
    
    // Atualização Otimista (Visual)
    const oldLeads = [...leads];
    setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));

    try {
      await fetch(`/api/marketing/leads/${leadId}/move`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        },
        body: JSON.stringify({ status: newStatus })
      });
    } catch (error) { setLeads(oldLeads); } // Reverte se der erro
  };

  const getColumnLeads = (status: string) => leads.filter(l => l.status === status);

  if (loading) return <div className="flex h-screen items-center justify-center bg-gray-50"><Loader2 className="animate-spin text-blue-600" size={48} /></div>;

  return (
    <div className="p-8 w-full h-screen overflow-hidden flex flex-col bg-gray-50 relative font-sans">
      
      {/* HEADER + TÍTULO */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-6 flex-shrink-0">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Funil de Vendas & Ads</h1>
          <p className="text-gray-500 font-medium">Gerencie leads e acompanhe sua performance no Meta Ads.</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="px-6 py-3 bg-blue-600 text-white rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-blue-700 flex items-center gap-2 shadow-xl shadow-blue-100 transition-all active:scale-95">
            <Plus size={18} /> Novo Lead
        </button>
      </header>

      {/* --- WIDGET DE INTEGRAÇÃO FACEBOOK (HEADER) --- */}
      <div className="mb-6 flex-shrink-0">
        {!isConnected ? (
            // ESTADO 1: NÃO CONECTADO
            <div className="bg-white p-4 rounded-3xl border border-gray-200 shadow-sm flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="bg-blue-100 p-3 rounded-2xl text-blue-600"><Target size={24} /></div>
                    <div>
                        <h3 className="font-bold text-gray-800">Ativar Tráfego Pago</h3>
                        <p className="text-xs text-gray-500">Conecte sua conta para importar leads automaticamente.</p>
                    </div>
                </div>
                <button 
                    onClick={handleFacebookLogin} 
                    disabled={authLoading}
                    className="flex items-center gap-2 px-5 py-2.5 bg-[#1877F2] text-white rounded-xl font-bold text-xs uppercase tracking-wider hover:bg-[#166fe5] transition-colors"
                >
                    {authLoading ? <Loader2 className="animate-spin" size={16} /> : <Facebook size={16} />}
                    Vincular Facebook
                </button>
            </div>
        ) : (
            // ESTADO 2: CONECTADO (DASHBOARD ADS)
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-3xl border border-blue-100 shadow-sm flex flex-col justify-between relative overflow-hidden group">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:scale-110 transition-transform"><Target size={40} /></div>
                    <span className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Investimento</span>
                    <div className="flex items-center gap-2 text-2xl font-black text-gray-800">
                        R$ {adsStats.spend.toFixed(2)}
                    </div>
                </div>
                <div className="bg-white p-4 rounded-3xl border border-purple-100 shadow-sm flex flex-col justify-between relative overflow-hidden group">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:scale-110 transition-transform"><TrendingUp size={40} /></div>
                    <span className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Cliques no Anúncio</span>
                    <div className="flex items-center gap-2 text-2xl font-black text-gray-800">
                        {adsStats.clicks}
                    </div>
                </div>
                <div className="bg-white p-4 rounded-3xl border border-green-100 shadow-sm flex flex-col justify-between relative overflow-hidden group">
                    <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:scale-110 transition-transform"><DollarSign size={40} /></div>
                    <span className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Custo por Clique</span>
                    <div className="flex items-center gap-2 text-2xl font-black text-gray-800">
                        R$ {adsStats.cpc.toFixed(2)}
                    </div>
                </div>
                <div className="bg-gradient-to-br from-green-500 to-emerald-600 p-4 rounded-3xl shadow-lg shadow-green-200 flex flex-col justify-center items-center text-white cursor-pointer hover:shadow-xl transition-all" onClick={checkMetaConnection}>
                    <RefreshCw size={24} className="mb-2 opacity-80" />
                    <span className="text-[10px] font-black uppercase tracking-widest opacity-80">Sincronizar</span>
                    <span className="font-bold text-sm">Atualizar Dados</span>
                </div>
            </div>
        )}
      </div>

      {/* --- KANBAN BOARD (CORPO DA PÁGINA) --- */}
      
      {/* MODAL NOVO LEAD */}
      {isModalOpen && (
          <div className="fixed inset-0 z-[100] bg-slate-900/60 flex items-center justify-center backdrop-blur-sm p-4">
              <div className="bg-white p-8 rounded-[2.5rem] shadow-2xl w-full max-w-md animate-in fade-in zoom-in duration-200 border border-white">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xl font-black text-gray-800">Novo Potencial Paciente</h3>
                      <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
                        <X size={20} className="text-gray-400" />
                      </button>
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
                        <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Origem do Lead</label>
                        <select className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all" value={newLead.source} onChange={e => setNewLead({...newLead, source: e.target.value})}>
                            <option value="Instagram">Instagram (Chatbot)</option>
                            <option value="Google">Google Ads</option>
                            <option value="Facebook">Facebook</option>
                            <option value="Indicação">Indicação Direta</option>
                        </select>
                      </div>
                      <button type="submit" className="w-full bg-blue-600 text-white py-4 rounded-2xl font-black text-sm uppercase tracking-widest mt-4 shadow-lg shadow-blue-100 hover:bg-blue-700 transition-all">Salvar Lead</button>
                  </form>
              </div>
          </div>
      )}

      {/* ÁREA DE ARRASTAR E SOLTAR */}
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="flex-1 overflow-x-auto overflow-y-hidden pb-4">
          <div className="flex gap-6 h-full min-w-[1200px]">
            {Object.entries(COLUMNS).map(([columnId, config]) => {
              const columnItems = getColumnLeads(columnId);
              return (
                <div key={columnId} className="flex flex-col bg-gray-200/30 rounded-[2rem] w-80 h-full max-h-full border border-gray-200/50">
                  <div className={`bg-white p-5 rounded-t-[2rem] border-b border-gray-100 flex justify-between items-center border-t-8 ${config.color} shadow-sm`}>
                    <div className="flex items-center gap-3">
                      <span className={`font-black text-xs uppercase tracking-widest ${config.headerColor}`}>{config.title}</span>
                      <span className="bg-gray-100 text-gray-500 text-[10px] px-2 py-0.5 rounded-lg font-black">{columnItems.length}</span>
                    </div>
                  </div>
                  <Droppable droppableId={columnId}>
                    {(provided, snapshot) => (
                      <div {...provided.droppableProps} ref={provided.innerRef} className={`flex-1 p-4 flex flex-col gap-4 overflow-y-auto transition-colors ${snapshot.isDraggingOver ? 'bg-blue-50/40' : ''}`}>
                        {columnItems.map((item, index) => (
                          <Draggable key={item.id} draggableId={item.id.toString()} index={index}>
                            {(provided, snapshot) => (
                              <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} className={`bg-white p-5 rounded-3xl border border-gray-100 group hover:border-blue-300 transition-all ${snapshot.isDragging ? 'shadow-2xl ring-4 ring-blue-500/10 z-50' : 'shadow-sm'}`} style={provided.draggableProps.style}>
                                <div className="flex justify-between items-start mb-3">
                                  <div className="font-bold text-gray-800 text-sm leading-tight">{item.name}</div>
                                  <button className="p-1 hover:bg-gray-50 rounded-lg text-gray-300"><MoreHorizontal size={14} /></button>
                                </div>
                                <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-tighter text-gray-400 mb-4">
                                  <div className={`w-1.5 h-1.5 rounded-full ${item.source === 'Instagram' ? 'bg-purple-500' : 'bg-blue-500'}`}></div>
                                  {item.source}
                                </div>
                                <div className="flex justify-between items-center pt-4 border-t border-gray-50">
                                   <button 
                                      className="text-[10px] font-black uppercase tracking-widest text-green-600 flex items-center gap-2 hover:bg-green-50 px-3 py-1.5 rounded-xl transition-colors" 
                                      onClick={() => window.open(`https://wa.me/55${item.phone}`, '_blank')}
                                   >
                                      <Phone size={12} /> WhatsApp
                                   </button>
                                   <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center text-[8px] font-black text-gray-400">ID</div>
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </div>
              );
            })}
          </div>
        </div>
      </DragDropContext>
    </div>
  );
}