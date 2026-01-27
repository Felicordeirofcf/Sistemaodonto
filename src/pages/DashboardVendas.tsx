import { useState, useEffect } from 'react';
import { TrendingUp, MessageSquare, DollarSign, Target, ArrowRight, Users, AlertTriangle } from 'lucide-react';

export function DashboardVendas() {
  const [stats, setStats] = useState({
    leads_generated: 0,
    conversions: 0,
    conversion_rate: 0,
    revenue: 0,
    net_profit: 0
  });

  const [generalStats, setGeneralStats] = useState({
    patients: 0,
    low_stock: 0,
    appointments: 0
  });

  useEffect(() => {
    // Busca estatísticas de conversão do bot
    fetch('/api/dashboard/conversion-stats', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
    .then(res => res.json())
    .then(data => setStats(data))
    .catch(console.error);

    // Busca estatísticas gerais do consultório
    fetch('/api/dashboard/stats', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
    .then(res => res.json())
    .then(data => setGeneralStats(data))
    .catch(console.error);
  }, []);

  const StatCard = ({ title, value, icon: Icon, color, suffix = "" }: any) => (
    <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm transition-hover hover:shadow-md">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-xl ${color} bg-opacity-10 text-current`}>
          <Icon size={24} />
        </div>
      </div>
      <p className="text-sm text-gray-500 font-medium">{title}</p>
      <h3 className="text-2xl font-bold text-gray-800 mt-1">
        {suffix} {typeof value === 'number' ? value.toLocaleString('pt-BR') : value}
      </h3>
    </div>
  );

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Performance & Vendas</h1>
          <p className="text-gray-500">Métricas reais do seu Chatbot e Financeiro Odontológico.</p>
        </div>
        {generalStats.low_stock > 0 && (
          <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg border border-red-100 flex items-center gap-2 animate-pulse">
            <AlertTriangle size={18} />
            <span className="text-sm font-bold">{generalStats.low_stock} itens em estoque baixo!</span>
          </div>
        )}
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total de Pacientes" value={generalStats.patients} icon={Users} color="text-gray-600 bg-gray-600" />
        <StatCard title="Faturamento Bot" value={stats.revenue} icon={DollarSign} color="text-green-600 bg-green-600" suffix="R$" />
        <StatCard title="Lucro Líquido Real" value={stats.net_profit} icon={TrendingUp} color="text-blue-600 bg-blue-600" suffix="R$" />
        <StatCard title="Taxa de Conversão" value={stats.conversion_rate.toFixed(1)} icon={Target} color="text-purple-600 bg-purple-600" suffix="%" />
      </div>

      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-3xl p-8 text-white flex justify-between items-center shadow-xl shadow-blue-200">
        <div>
          <h2 className="text-2xl font-bold mb-2">Automação Ativa</h2>
          <p className="opacity-90 max-w-md">O Chatbot captou <b>{stats.leads_generated} leads</b> este mês, resultando em <b>{stats.conversions} agendamentos</b> diretos na sua agenda.</p>
        </div>
        <button className="bg-white text-blue-600 px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-gray-50 transition-all">
          Ver Leads no CRM <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}