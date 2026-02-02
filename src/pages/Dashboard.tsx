import { useState, useEffect } from 'react';
import { 
  Users, DollarSign, Activity, 
  TrendingUp, TrendingDown, Clock, ArrowRight, Loader2, Sparkles 
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
// Se ainda não tiver o SystemTour, comente a linha abaixo para evitar erros
// import { SystemTour } from '../components/SystemTour'; 

interface DashboardStats {
  patients: number;
  revenue: number;
  low_stock: number;
  appointments: number;
  net_profit?: number;
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    patients: 0,
    revenue: 0,
    low_stock: 0,
    appointments: 0,
    net_profit: 0
  });
  const [loading, setLoading] = useState(true);
  
  // Exemplo de dados para o gráfico (pode vir do backend futuramente)
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
    
    // Busca dados reais do Backend
    fetch('/api/dashboard/stats', {
        headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Erro ao carregar dados');
        return res.json();
      })
      .then(data => {
        setStats(data);
      })
      .catch(err => {
        console.error("Usando dados offline:", err);
        // Mantém zeros ou dados de cache se falhar
      })
      .finally(() => setLoading(false));
  }, []);

  const formatCurrency = (value: number | undefined) => 
    (value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const Card = ({ title, value, icon: Icon, color, trend, id }: any) => (
    <div id={id} className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100 hover:shadow-xl transition-all group">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-4 rounded-2xl ${color} bg-opacity-10 group-hover:scale-110 transition-transform`}>
          <Icon className={color.replace('bg-', 'text-')} size={28} />
        </div>
        {trend && (
          <span className={`flex items-center text-[10px] font-black uppercase ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? <TrendingUp size={14} className="mr-1"/> : <TrendingDown size={14} className="mr-1"/>}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <h3 className="text-gray-400 text-[10px] font-black uppercase tracking-[0.15em] mb-1">{title}</h3>
      <p className="text-2xl font-black text-gray-800 tracking-tighter">{value}</p>
    </div>
  );

  if (loading) return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <Loader2 className="animate-spin text-blue-600" size={48} />
    </div>
  );

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      
      {/* Se tiver o componente SystemTour, descomente abaixo */}
      {/* <SystemTour /> */}

      <header className="mb-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-4xl font-black text-gray-900 tracking-tight">Visão Geral</h1>
          <p className="text-gray-500 font-medium mt-1 italic">Bem-vindo ao centro de comando.</p>
        </div>
        <div className="flex items-center gap-2 bg-blue-50 text-blue-600 px-4 py-2 rounded-2xl border border-blue-100 font-black text-[10px] uppercase tracking-widest">
          <Sparkles size={14} /> Sistema Inteligente Ativo
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <Card title="Pacientes Totais" value={stats.patients} icon={Users} color="bg-blue-600" trend={+12} />
        <Card title="Receita Total" value={formatCurrency(stats.revenue)} icon={DollarSign} color="bg-green-600" trend={+15} />
        <Card id="estoque-alertas" title="Estoque Baixo" value={stats.low_stock} icon={Activity} color="bg-red-600" />
        <Card title="Consultas Hoje" value={stats.appointments} icon={Clock} color="bg-purple-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        {/* Gráfico de Receita */}
        <div className="lg:col-span-2 bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-xl font-black text-gray-800 tracking-tight">Performance Financeira</h2>
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-600"></div>
              <span className="text-[10px] font-black uppercase text-gray-400">Receita Semanal</span>
            </div>
          </div>
          
          {/* CORREÇÃO AQUI: Style inline garante altura para o Recharts não quebrar */}
          <div style={{ width: '100%', height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorValor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 10, fontWeight: 900}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 10, fontWeight: 900}} tickFormatter={(value) => `R$${value/1000}k`} />
                <Tooltip 
                  contentStyle={{borderRadius: '24px', border: 'none', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', padding: '16px'}}
                  formatter={(value: any) => [formatCurrency(value), 'Receita']}
                />
                <Area type="monotone" dataKey="valor" stroke="#2563eb" strokeWidth={4} fillOpacity={1} fill="url(#colorValor)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Fila de Espera (Mock) */}
        <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 flex flex-col">
          <h2 className="text-xl font-black text-gray-800 mb-6 tracking-tight">Fila de Espera</h2>
          <div className="space-y-6 flex-1">
              {[
                { name: 'Carlos Eduardo', time: '14:00', type: 'Avaliação' },
                { name: 'Mariana Souza', time: '15:30', type: 'Clareamento' },
                { name: 'Roberto Lima', time: '17:00', type: 'Extração' }
              ].map((patient, i) => (
               <div key={i} className="flex items-center gap-4 p-4 hover:bg-gray-50 rounded-3xl transition-all cursor-pointer group border border-transparent hover:border-gray-100">
                  <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center font-black text-sm">
                    {patient.name.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-black text-sm text-gray-800 leading-none mb-1">{patient.name}</h4>
                    <div className="flex items-center text-[10px] font-bold text-gray-400 uppercase tracking-tighter gap-2">
                      <Clock size={12} className="text-blue-500" /> {patient.time} — {patient.type}
                    </div>
                  </div>
                  <ArrowRight size={18} className="text-gray-200 group-hover:text-blue-500 group-hover:translate-x-1 transition-all"/>
               </div>
              ))}
          </div>
          <button className="w-full mt-8 py-4 rounded-2xl bg-gray-900 text-white font-black text-[10px] uppercase tracking-[0.2em] hover:bg-black transition-colors shadow-lg shadow-gray-200">
            Gerenciar Agenda
          </button>
        </div>
      </div>
    </div>
  );
}