import { useState, useEffect } from 'react';
import { 
  Users, DollarSign, Calendar, Activity, 
  TrendingUp, TrendingDown, Clock, ArrowRight 
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';

interface DashboardStats {
  total_patients: number;
  today_revenue: number;
  low_stock_items: number;
  active_treatments: number;
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_patients: 0,
    today_revenue: 0,
    low_stock_items: 0,
    active_treatments: 0
  });

  // Dados fictícios para o gráfico (até implementarmos o histórico real)
  const data = [
    { name: 'Seg', valor: 4000 },
    { name: 'Ter', valor: 3000 },
    { name: 'Qua', valor: 2000 },
    { name: 'Qui', valor: 2780 },
    { name: 'Sex', valor: 1890 },
    { name: 'Sab', valor: 2390 },
  ];

  useEffect(() => {
    const token = localStorage.getItem('odonto_token');
    fetch('/api/dashboard/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Erro ao carregar dashboard:", err));
  }, []);

  const Card = ({ title, value, icon: Icon, color, trend }: any) => (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-xl ${color} bg-opacity-10`}>
          <Icon className={color.replace('bg-', 'text-')} size={24} />
        </div>
        {trend && (
          <span className={`flex items-center text-xs font-bold ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? <TrendingUp size={14} className="mr-1"/> : <TrendingDown size={14} className="mr-1"/>}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <h3 className="text-gray-500 text-sm font-medium mb-1">{title}</h3>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
    </div>
  );

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-800">Visão Geral</h1>
        <p className="text-gray-500 text-sm">Bem-vindo de volta, Dr(a). chefe.</p>
      </div>

      {/* STATS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card 
          title="Pacientes Totais" 
          value={stats.total_patients} 
          icon={Users} 
          color="bg-blue-500" 
          trend={+12}
        />
        <Card 
          title="Faturamento Dia" 
          value={`R$ ${stats.today_revenue}`} 
          icon={DollarSign} 
          color="bg-green-500" 
          trend={+15}
        />
        <Card 
          title="Itens Baixo Estoque" 
          value={stats.low_stock_items} 
          icon={Activity} 
          color="bg-orange-500" 
        />
        <Card 
          title="Tratamentos Hoje" 
          value={stats.active_treatments} 
          icon={Activity} 
          color="bg-purple-500" 
        />
      </div>

      {/* CHART SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-bold text-gray-800">Receita Semanal</h2>
            <button className="text-blue-600 text-sm font-bold hover:underline">Ver Relatório</button>
          </div>
          
          {/* CORREÇÃO DO ERRO DE CHART: Adicionada altura fixa (h-80) */}
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorValor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} tickFormatter={(value) => `R$${value/1000}k`} />
                <Tooltip 
                  contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                />
                <Area type="monotone" dataKey="valor" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorValor)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SIDE WIDGET */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Próximas Consultas</h2>
          <div className="space-y-4">
             {/* Lista fake para visual */}
             {[1,2,3].map((_, i) => (
               <div key={i} className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-xl transition-colors cursor-pointer group">
                  <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-xs">PF</div>
                  <div className="flex-1">
                    <h4 className="font-bold text-sm text-gray-800">Paciente Fictício</h4>
                    <div className="flex items-center text-xs text-gray-500 gap-1">
                      <Clock size={10} /> 14:00 - Limpeza
                    </div>
                  </div>
                  <ArrowRight size={16} className="text-gray-300 group-hover:text-blue-500 transition-colors"/>
               </div>
             ))}
          </div>
          <button className="w-full mt-6 py-3 rounded-xl border border-blue-100 text-blue-600 font-bold text-sm hover:bg-blue-50 transition-colors">
            Ver Agenda Completa
          </button>
        </div>
      </div>
    </div>
  );
}