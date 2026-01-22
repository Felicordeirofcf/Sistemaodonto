import { MoreHorizontal, Plus, Search, Bell, Filter, Megaphone, Calendar } from 'lucide-react';

// --- AQUI ESTÁ A CORREÇÃO (Tipagem) ---
interface KanbanItem {
  id: number;
  name: string;
  origin?: string;    // O ? significa que é opcional
  time?: string;
  status?: string;
  date?: string;
  info?: string;
  tag?: string;
  tagColor?: string;
}

interface KanbanColumn {
  title: string;
  color: string;
  headerColor: string;
  count: number;
  items: KanbanItem[];
}
// --------------------------------------

const columns: KanbanColumn[] = [
  {
    title: 'Novos Leads',
    color: 'border-t-4 border-blue-500',
    headerColor: 'text-blue-600',
    count: 12,
    items: [
      { id: 1, name: 'João Souza', origin: 'Instagram Ads - Botox', time: '2h atrás' },
      { id: 2, name: 'Maria Lima', origin: 'Facebook - Preenchimento', time: '5h atrás' },
      { id: 21, name: 'Carlos Mendes', origin: 'Google Ads - Lentes', time: '1d atrás' },
    ]
  },
  {
    title: 'Agendamento Tentado',
    color: 'border-t-4 border-yellow-500',
    headerColor: 'text-yellow-600',
    count: 5,
    items: [
      { id: 3, name: 'Henrique Santos', status: 'Sem resposta (Zap)', date: 'Hoje' },
      { id: 4, name: 'Patricia Gomes', status: 'Caixa Postal', date: 'Ontem' },
    ]
  },
  {
    title: 'Consulta Agendada',
    color: 'border-t-4 border-green-500',
    headerColor: 'text-green-600',
    count: 8,
    items: [
      { id: 5, name: 'Fernanda Rocha', info: '15/08 às 10:00', tag: 'Confirmado', tagColor: 'bg-green-100 text-green-700' },
      { id: 52, name: 'Paulo Almeida', info: '16/08 às 14:30', tag: 'Pendente', tagColor: 'bg-yellow-100 text-yellow-700' },
    ]
  },
  {
    title: 'Em Tratamento',
    color: 'border-t-4 border-purple-500',
    headerColor: 'text-purple-600',
    count: 24,
    items: [
      { id: 6, name: 'Roberta Martins', status: 'Ortodontia (Mês 3)' },
      { id: 7, name: 'André Silva', status: 'Clareamento (Sessão 2)' },
    ]
  }
];

export function MarketingCRM() {
  return (
    <div className="p-8 w-full">
      {/* Header Superior */}
      <header className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-primary">Marketing & CRM</h1>
          <p className="text-gray-500 mt-1">Gestão de leads e acompanhamento comercial</p>
        </div>
        <div className="flex gap-4">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input 
                    type="text" 
                    placeholder="Buscar paciente..." 
                    className="pl-10 pr-4 py-2 rounded-full border border-gray-200 focus:outline-none focus:border-primary w-64"
                />
            </div>
            <button className="p-2 bg-white border border-gray-200 rounded-full text-gray-600 hover:bg-gray-50 relative">
                <Bell size={20} />
                <span className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full border-2 border-white"></span>
            </button>
        </div>
      </header>

      {/* Barra de Status da Campanha */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-500 text-white p-5 rounded-xl flex justify-between items-center mb-8 shadow-lg shadow-blue-200">
        <div className="flex items-center gap-4">
          <div className="bg-white/20 p-3 rounded-lg">
             <Megaphone size={24} className="text-white" />
          </div>
          <div>
            <h3 className="font-bold text-lg">Campanha: Clareamento de Verão</h3>
            <p className="text-blue-100 text-sm">45 Leads capturados esta semana • Meta: 60</p>
          </div>
        </div>
        <div className="flex gap-2">
            <button className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-semibold transition-colors">
                Ver Relatório
            </button>
            <button className="p-2 hover:bg-white/20 rounded-lg"><MoreHorizontal /></button>
        </div>
      </div>

      {/* Filtros rápidos */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-2">
            <button className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 flex items-center gap-2">
                <Filter size={16} /> Todos os Canais
            </button>
            <button className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">
                Instagram
            </button>
            <button className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">
                Google Ads
            </button>
        </div>
        <button className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 flex items-center gap-2 shadow-lg shadow-primary/30">
            <Plus size={18} /> Novo Lead
        </button>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-start h-[calc(100vh-340px)] overflow-x-auto">
        {columns.map((col) => (
          <div key={col.title} className="flex flex-col bg-gray-50/50 rounded-xl h-full">
            {/* Título da Coluna */}
            <div className={`bg-white p-4 rounded-t-xl shadow-sm border-b border-gray-100 flex justify-between items-center ${col.color}`}>
              <div className="flex items-center gap-2">
                <span className={`font-bold ${col.headerColor}`}>{col.title}</span>
                <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full font-bold">{col.count}</span>
              </div>
              <Plus size={18} className="text-gray-400 cursor-pointer hover:text-primary" />
            </div>

            {/* Area de Cards com Scroll */}
            <div className="flex-1 p-3 flex flex-col gap-3 overflow-y-auto">
              {col.items.map((item) => (
                <div key={item.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md hover:border-blue-200 transition-all cursor-pointer group">
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-bold text-gray-800 group-hover:text-primary transition-colors">{item.name}</div>
                    <MoreHorizontal size={16} className="text-gray-300 hover:text-gray-600" />
                  </div>
                  
                  {item.origin && (
                    <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
                        <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                        {item.origin}
                    </div>
                  )}
                  
                  {item.status && <div className="text-sm text-gray-600 font-medium">{item.status}</div>}
                  
                  {item.info && (
                    <div className="flex items-center gap-2 text-sm text-gray-600 my-2 bg-gray-50 p-2 rounded">
                      <Calendar size={14} /> {item.info}
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-50">
                     {item.tag ? (
                        <span className={`text-[10px] px-2 py-1 rounded-full font-bold uppercase tracking-wider ${item.tagColor}`}>
                        {item.tag}
                        </span>
                     ) : <span></span>}
                     
                     {(item.time || item.date) && (
                        <span className="text-xs text-gray-400 font-medium">
                            {item.time || item.date}
                        </span>
                     )}
                  </div>
                </div>
              ))}
              
              <button className="w-full py-2 border-2 border-dashed border-gray-200 rounded-lg text-gray-400 text-sm font-medium hover:border-primary/50 hover:text-primary hover:bg-blue-50/50 transition-all">
                + Adicionar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}