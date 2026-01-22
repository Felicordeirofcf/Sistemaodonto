import { ArrowUp, ArrowDown, Calendar, Users, DollarSign, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Dados simulados para o gráfico (Receita Mensal)
const data = [
  { name: 'Jan', receita: 4000 },
  { name: 'Fev', receita: 5500 },
  { name: 'Mar', receita: 6000 },
  { name: 'Abr', receita: 8000 },
  { name: 'Mai', receita: 11000 },
  { name: 'Jun', receita: 9500 },
];

const kpiCards = [
  { title: 'Faturamento Hoje', value: 'R$ 12.500', change: '+15%', isPositive: true, icon: DollarSign, color: 'bg-blue-500' },
  { title: 'Agendamentos', value: '18', sub: '(4 Novos)', isPositive: true, icon: Calendar, color: 'bg-purple-500' },
  { title: 'Ticket Médio', value: 'R$ 690', change: '-2%', isPositive: false, icon: Activity, color: 'bg-orange-500' },
  { title: 'Contas a Receber', value: 'R$ 45.000', change: '+5%', isPositive: true, icon: Users, color: 'bg-green-500' },
];

const nextAppointments = [
  { id: 1, name: 'Ana Silva', proc: 'Harmonização Facial', time: '09:00', img: 'https://i.pravatar.cc/150?img=1' },
  { id: 2, name: 'Pedro Rocha', proc: 'Limpeza Dental', time: '09:30', img: 'https://i.pravatar.cc/150?img=11' },
  { id: 3, name: 'Laura Mendes', proc: 'Clareamento Dental', time: '10:15', img: 'https://i.pravatar.cc/150?img=5' },
  { id: 4, name: 'Carlos Lima', proc: 'Implante Dentário', time: '11:00', img: 'https://i.pravatar.cc/150?img=3' },
];

export function Dashboard() {
  return (
    <div className="p-8 w-full">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary">Bom dia, Dr. Fonseca</h1>
        <p className="text-gray-500">Aqui está o resumo da sua clínica hoje.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {kpiCards.map((card, index) => (
          <div key={index} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-gray-500 text-sm font-medium">{card.title}</p>
                <h3 className="text-2xl font-bold text-slate-800 mt-1">{card.value} <span className="text-sm font-normal text-gray-400">{card.sub}</span></h3>
              </div>
              <div className={`p-2 rounded-lg ${card.color} bg-opacity-10`}>
                <card.icon className={card.color.replace('bg-', 'text-')} size={24} />
              </div>
            </div>
            
            {card.change && (
              <div className={`flex items-center gap-1 mt-4 text-sm font-medium ${card.isPositive ? 'text-green-600' : 'text-red-500'}`}>
                {card.isPositive ? <ArrowUp size={16} /> : <ArrowDown size={16} />}
                {card.change} 
                <span className="text-gray-400 ml-1 font-normal">vs ontem</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Gráfico Principal */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Receita Mensal</h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af'}} tickFormatter={(value) => `R$${value/1000}k`} />
                <Tooltip 
                  cursor={{fill: '#f4f6f8'}}
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                />
                <Bar dataKey="receita" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Lista Lateral (Próximos Atendimentos) */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Próximos Atendimentos</h3>
          <div className="flex flex-col gap-4">
            {nextAppointments.map((item) => (
              <div key={item.id} className="flex items-center gap-4 p-3 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer group">
                <img src={item.img} alt={item.name} className="w-12 h-12 rounded-full object-cover border-2 border-transparent group-hover:border-primary transition-all" />
                <div className="flex-1">
                  <h4 className="font-bold text-slate-800">{item.name}</h4>
                  <p className="text-sm text-gray-500">{item.proc}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-primary">{item.time}</p>
                </div>
              </div>
            ))}
            
            <button className="w-full mt-4 py-3 bg-gray-50 text-primary font-semibold rounded-lg hover:bg-blue-50 transition-colors">
              Ver Agenda Completa
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}