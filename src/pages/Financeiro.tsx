import { useState } from 'react';
import { TrendingUp, TrendingDown, Wallet, ArrowUpRight, ArrowDownRight, Filter, Download } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function Financeiro() {
  const data = [
    { name: 'Jan', entrada: 12500, saida: 4200 }, { name: 'Fev', entrada: 15000, saida: 5100 },
    { name: 'Mar', entrada: 18200, saida: 6000 }, { name: 'Abr', entrada: 14000, saida: 4800 },
    { name: 'Mai', entrada: 21000, saida: 7500 }, { name: 'Jun', entrada: 25400, saida: 8200 },
  ];

  const transactions = [
    { id: 1, paciente: 'Maria Silva', proc: 'Implante', valor: 3500, tipo: 'entrada', status: 'pago' },
    { id: 2, paciente: 'Dental Cremer', proc: 'Materiais', valor: 1250, tipo: 'saida', status: 'pago' },
    { id: 3, paciente: 'João Souza', proc: 'Manutenção', valor: 150, tipo: 'entrada', status: 'pendente' },
    { id: 4, paciente: 'Ana Paula', proc: 'Botox', valor: 1200, tipo: 'entrada', status: 'atrasado' },
    { id: 5, paciente: 'Lab. Pro', proc: 'Prótese', valor: 800, tipo: 'saida', status: 'pendente' },
  ];

  const [periodo, setPeriodo] = useState('mensal');

  return (
    <div className="p-4 md:p-6 bg-gray-50 min-h-screen text-sm">
      <header className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Financeiro</h1>
          <p className="text-gray-500 text-xs">Visão geral do fluxo de caixa.</p>
        </div>
        <div className="flex gap-2">
           <button className="flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-200 rounded-md text-gray-600 hover:bg-gray-50 text-xs font-medium">
             <Filter size={14}/> Filtrar
           </button>
           <button className="flex items-center gap-1 px-3 py-1.5 bg-primary text-white rounded-md hover:bg-blue-700 shadow-sm text-xs font-medium">
             <Download size={14}/> Exportar
           </button>
        </div>
      </header>

      {/* CARDS COMPACTOS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-start mb-2">
            <p className="text-xs font-medium text-gray-500">Entradas</p>
            <div className="p-1.5 bg-green-50 rounded text-green-600"><TrendingUp size={16} /></div>
          </div>
          <h3 className="text-2xl font-bold text-gray-800">R$ 25.400</h3>
          <span className="text-xs text-green-600 flex items-center gap-1 mt-1 font-medium"><ArrowUpRight size={12}/> +12%</span>
        </div>

        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-start mb-2">
            <p className="text-xs font-medium text-gray-500">Saídas</p>
            <div className="p-1.5 bg-red-50 rounded text-red-600"><TrendingDown size={16} /></div>
          </div>
          <h3 className="text-2xl font-bold text-gray-800">R$ 8.200</h3>
          <span className="text-xs text-red-600 flex items-center gap-1 mt-1 font-medium"><ArrowDownRight size={12}/> +5%</span>
        </div>

        <div className="bg-gray-900 p-4 rounded-xl shadow-lg text-white">
          <div className="flex justify-between items-start mb-2">
            <p className="text-xs font-medium text-gray-400">Lucro Líquido</p>
            <div className="p-1.5 bg-gray-700 rounded text-white"><Wallet size={16} /></div>
          </div>
          <h3 className="text-2xl font-bold">R$ 17.200</h3>
          <span className="text-xs text-gray-300 flex items-center gap-1 mt-1"><div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div> Positivo</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* GRÁFICO MAIS BAIXO */}
        <div className="lg:col-span-2 bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-gray-800 text-sm">Evolução</h3>
            <div className="flex bg-gray-50 rounded p-0.5">
              <button onClick={() => setPeriodo('mensal')} className={`px-2 py-0.5 text-[10px] rounded font-medium transition-all ${periodo === 'mensal' ? 'bg-white shadow text-gray-800' : 'text-gray-500'}`}>Mensal</button>
              <button onClick={() => setPeriodo('anual')} className={`px-2 py-0.5 text-[10px] rounded font-medium transition-all ${periodo === 'anual' ? 'bg-white shadow text-gray-800' : 'text-gray-500'}`}>Anual</button>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 10}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 10}} tickFormatter={(value) => `R$${value/1000}k`} />
                <Tooltip cursor={{fill: '#f9fafb'}} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', fontSize: '12px'}} />
                <Bar dataKey="entrada" fill="#0ea5e9" radius={[2, 2, 0, 0]} barSize={24} />
                <Bar dataKey="saida" fill="#ef4444" radius={[2, 2, 0, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* LISTA COMPACTA */}
        <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100">
          <h3 className="font-bold text-gray-800 text-sm mb-4">Lançamentos</h3>
          <div className="space-y-3">
            {transactions.map((t) => (
              <div key={t.id} className="flex items-center justify-between py-1 border-b border-gray-50 last:border-0">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${t.tipo === 'entrada' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                    {t.tipo === 'entrada' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-gray-800">{t.paciente}</p>
                    <p className="text-[10px] text-gray-500">{t.proc}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-xs font-bold ${t.tipo === 'entrada' ? 'text-green-600' : 'text-red-600'}`}>
                    {t.tipo === 'entrada' ? '+' : '-'} R$ {t.valor}
                  </p>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-medium uppercase ${t.status === 'pago' ? 'bg-green-50 text-green-700' : t.status === 'pendente' ? 'bg-yellow-50 text-yellow-700' : 'bg-red-50 text-red-700'}`}>
                    {t.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}