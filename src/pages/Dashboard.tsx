import { Users, Calendar, DollarSign, Activity, ArrowUpRight, TrendingUp, Clock } from 'lucide-react';

export function Dashboard() {
  const stats = [
    { label: 'Pacientes Hoje', value: '12', icon: Users, color: 'text-blue-600', bg: 'bg-blue-50', change: '+2' },
    { label: 'Faturamento Dia', value: 'R$ 4.250', icon: DollarSign, color: 'text-green-600', bg: 'bg-green-50', change: '+15%' },
    { label: 'Agendamentos', value: '45', icon: Calendar, color: 'text-purple-600', bg: 'bg-purple-50', change: '+5' },
    { label: 'Tratamentos', value: '8', icon: Activity, color: 'text-orange-600', bg: 'bg-orange-50', change: 'Estável' },
  ];

  const appointments = [
    { time: '09:00', name: 'Maria Silva', type: 'Avaliação', status: 'Confirmado' },
    { time: '10:00', name: 'João Santos', type: 'Canal', status: 'Em andamento' },
    { time: '11:00', name: 'Ana Costa', type: 'Limpeza', status: 'Pendente' },
    { time: '14:00', name: 'Pedro H.', type: 'Botox', status: 'Confirmado' },
  ];

  return (
    <div className="p-4 md:p-6 bg-gray-50 min-h-screen font-sans text-sm">
      <header className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Visão Geral</h1>
        <p className="text-xs text-gray-500">Bem-vindo de volta, Dr. Fonseca.</p>
      </header>

      {/* STATS GRID - Mais compacto */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white p-3 rounded-xl border border-gray-100 shadow-sm flex flex-col justify-between">
            <div className="flex justify-between items-start mb-2">
              <div className={`p-1.5 rounded-lg ${stat.bg} ${stat.color}`}>
                <stat.icon size={16} />
              </div>
              <span className="text-[10px] font-medium bg-gray-50 px-1.5 py-0.5 rounded text-gray-600 flex items-center gap-1">
                <TrendingUp size={10} /> {stat.change}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-800 leading-tight">{stat.value}</h3>
              <p className="text-[10px] text-gray-500 font-medium uppercase tracking-wide mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AGENDA DO DIA */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-gray-800 flex items-center gap-2">
              <Calendar size={16} className="text-gray-400"/> Agenda de Hoje
            </h3>
            <button className="text-xs text-primary font-medium hover:underline">Ver completa</button>
          </div>
          
          <div className="space-y-2">
            {appointments.map((app, i) => (
              <div key={i} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg transition-colors border border-transparent hover:border-gray-100 group">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-gray-600 bg-gray-100 px-2 py-1 rounded">{app.time}</span>
                  <div>
                    <p className="font-bold text-gray-800">{app.name}</p>
                    <p className="text-[10px] text-gray-500">{app.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                   <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                     app.status === 'Confirmado' ? 'bg-green-50 text-green-700' : 
                     app.status === 'Em andamento' ? 'bg-blue-50 text-blue-700' : 'bg-yellow-50 text-yellow-700'
                   }`}>
                     {app.status}
                   </span>
                   <button className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-gray-600">
                     <ArrowUpRight size={14} />
                   </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ATIVIDADE RECENTE / LEMBRETES */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
           <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
             <Clock size={16} className="text-gray-400"/> Avisos Rápidos
           </h3>
           <div className="space-y-3">
             <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
               <p className="text-xs text-blue-800 font-bold mb-1">Reposição de Estoque</p>
               <p className="text-[10px] text-blue-600">Anestésicos acabando. Fazer pedido até sexta.</p>
             </div>
             <div className="p-3 bg-orange-50 rounded-lg border border-orange-100">
               <p className="text-xs text-orange-800 font-bold mb-1">Prótese Pendente</p>
               <p className="text-[10px] text-orange-600">Cobrar laboratório sobre o caso da D. Lourdes.</p>
             </div>
             <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
               <p className="text-xs text-gray-800 font-bold mb-1">Reunião Equipe</p>
               <p className="text-[10px] text-gray-500">Quinta-feira às 08:30.</p>
             </div>
           </div>
        </div>
      </div>
    </div>
  );
}