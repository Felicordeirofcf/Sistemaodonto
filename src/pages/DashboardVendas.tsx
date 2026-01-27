import { useState, useEffect } from 'react';
import { 
  TrendingUp, MessageSquare, DollarSign, Target, 
  ArrowRight, Users, AlertTriangle, Loader2, Filter 
} from 'lucide-react';

export function DashboardVendas() {
  const [stats, setStats] = useState({
    leads_generated: 0,
    conversions: 0,
    conversion_rate: 0,
    revenue: 0,
    net_profit: 0 // Campo de Lucro Real
  });

  const [generalStats, setGeneralStats] = useState({
    patients: 0,
    low_stock: 0,
    appointments: 0
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('odonto_token');
        const headers = { 'Authorization': `Bearer ${token}` };

        // 1. Busca estatísticas de performance do Bot e Vendas
        const resVendas = await fetch('/api/dashboard/conversion-stats', { headers });
        const dataVendas = await resVendas.json();

        // 2. Busca estatísticas gerais (sincronizado com seu dashboard principal)
        const resGeral = await fetch('/api/dashboard/stats', { headers });
        const dataGeral = await resGeral.json();

        setStats(dataVendas);
        // Ajuste das chaves para bater com o backend: patients, low_stock, appointments
        setGeneralStats({
          patients: dataGeral.patients || 0,
          low_stock: dataGeral.low_stock || 0,
          appointments: dataGeral.appointments || 0
        });
      } catch (error) {
        console.error("Erro ao carregar métricas:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const formatCurrency = (value: number) => 
    (value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const StatCard = ({ title, value, icon: Icon, color, isCurrency = false, isPercent = false }: any) => (
    <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm transition-all hover:shadow-lg hover:border-blue-100 group">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-2xl ${color} bg-opacity-10 transition-colors group-hover:bg-opacity-20`}>
          <Icon size={24} className={color.replace('bg-', 'text-')} />
        </div>
      </div>
      <p className="text-xs text-gray-400 font-black uppercase tracking-widest">{title}</p>
      <h3 className="text-2xl font-black text-gray-800 mt-1 tracking-tighter">
        {isCurrency ? formatCurrency(value) : isPercent ? `${value.toFixed(1)}%` : value}
      </h3>
    </div>
  );

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <Loader2 className="animate-spin text-blue-600" size={48} />
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">Performance & Vendas</h1>
          <p className="text-gray-500 font-medium">Métricas de conversão do seu Chatbot e Saúde Financeira.</p>
        </div>
        
        <div className="flex items-center gap-3">
          {generalStats.low_stock > 0 && (
            <div className="bg-red-50 text-red-600 px-4 py-2 rounded-2xl border border-red-100 flex items-center gap-2 animate-pulse">
              <AlertTriangle size={18} />
              <span className="text-xs font-black uppercase">{generalStats.low_stock} Itens Críticos</span>
            </div>
          )}
          <button className="p-2 bg-white border border-gray-200 rounded-xl text-gray-400 hover:text-blue-600 transition-colors">
            <Filter size={20} />
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard title="Base de Pacientes" value={generalStats.patients} icon={Users} color="bg-gray-600" />
        <StatCard title="Receita (Bot)" value={stats.revenue} icon={DollarSign} color="bg-green-600" isCurrency />
        <StatCard title="Lucro Real (ROI)" value={stats.net_profit} icon={TrendingUp} color="bg-blue-600" isCurrency />
        <StatCard title="Taxa de Conversão" value={stats.conversion_rate} icon={Target} color="bg-purple-600" isPercent />
      </div>

      {/* Hero CTA para o CRM */}
      <div className="bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-800 rounded-[2.5rem] p-10 text-white flex flex-col md:flex-row justify-between items-center shadow-2xl shadow-blue-900/20 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
        
        <div className="relative z-10 text-center md:text-left mb-8 md:mb-0">
          <h2 className="text-3xl font-black mb-3">Automação de Leads</h2>
          <p className="opacity-90 max-w-lg font-medium leading-relaxed">
            Este mês, sua IA captou <b className="text-blue-100">{stats.leads_generated} novos leads</b> através do Instagram/WhatsApp, gerando <b className="text-blue-100">{stats.conversions} novos agendamentos</b> automáticos na sua agenda.
          </p>
        </div>
        
        <button className="relative z-10 bg-white text-blue-700 px-8 py-4 rounded-2xl font-black text-sm uppercase tracking-widest shadow-xl hover:scale-105 transition-all flex items-center gap-3 active:scale-95">
          Gerenciar Funil <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}