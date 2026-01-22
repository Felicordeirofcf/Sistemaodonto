import { useState } from 'react';
import { 
  DollarSign, TrendingUp, TrendingDown, Wallet, 
  Calendar, ArrowUpRight, ArrowDownRight, Filter, Download 
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell 
} from 'recharts';

export function Financeiro() {
  // Dados Simulados para o Gráfico
  const data = [
    { name: 'Jan', entrada: 12500, saida: 4200 },
    { name: 'Fev', entrada: 15000, saida: 5100 },
    { name: 'Mar', entrada: 18200, saida: 6000 },
    { name: 'Abr', entrada: 14000, saida: 4800 },
    { name: 'Mai', entrada: 21000, saida: 7500 },
    { name: 'Jun', entrada: 25400, saida: 8200 },
  ];

  // Dados Simulados para a Tabela
  const transactions = [
    { id: 1, paciente: 'Maria Silva', proc: 'Implante Dentário', valor: 3500, tipo: 'entrada', status: 'pago', data: '22/06/2026' },
    { id: 2, paciente: 'Dental Cremer', proc: 'Compra de Materiais', valor: 1250, tipo: 'saida', status: 'pago', data: '21/06/2026' },
    { id: 3, paciente: 'João Souza', proc: 'Manutenção Aparelho', valor: 150, tipo: 'entrada', status: 'pendente', data: '20/06/2026' },
    { id: 4, paciente: 'Laboratório Pro', proc: 'Prótese Cerâmica', valor: 800, tipo: 'saida', status: 'pendente', data: '19/06/2026' },
    { id: 5, paciente: 'Ana Paula', proc: 'Harmonização Facial', valor: 1200, tipo: 'entrada', status: 'atrasado', data: '15/06/2026' },
  ];

  const [periodo, setPeriodo] = useState('mensal');

  return (
    <div className="p-6 md:p-8 bg-gray-50 min-h-screen">
      
      {/* CABEÇALHO */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Financeiro</h1>
          <p className="text-gray-500 text-sm mt-1">Visão geral do fluxo de caixa da clínica.</p>
        </div>
        
        <div className="flex gap-2">
           <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 text-sm">
             <Filter size={16}/> Filtrar
           </button>
           <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 shadow-lg shadow-blue-200 text-sm">
             <Download size={16}/> Exportar Relatório
           </button>
        </div>
      </header>

      {/* CARDS DE RESUMO */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        
        {/* Card 1: Faturamento */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-500 mb-1">Entradas (Junho)</p>
              <h3 className="text-3xl font-bold text-gray-800">R$ 25.400,00</h3>
            </div>
            <div className="p-3 bg-green-100 rounded-lg text-green-600">
              <TrendingUp size={24} />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm text-green-600 font-medium">
            <ArrowUpRight size={16} /> +12.5% vs mês anterior
          </div>
        </div>

        {/* Card 2: Despesas */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-500 mb-1">Saídas (Junho)</p>
              <h3 className="text-3xl font-bold text-gray-800">R$ 8.200,00</h3>
            </div>
            <div className="p-3 bg-red-100 rounded-lg text-red-600">
              <TrendingDown size={24} />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm text-red-600 font-medium">
            <ArrowDownRight size={16} /> +5% vs mês anterior
          </div>
        </div>

        {/* Card 3: Saldo */}
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-6 rounded-2xl shadow-lg text-white">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-gray-400 mb-1">Lucro Líquido</p>
              <h3 className="text-3xl font-bold">R$ 17.200,00</h3>
            </div>
            <div className="p-3 bg-gray-700 rounded-lg text-white">
              <Wallet size={24} />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-sm text-gray-300">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span> Caixa Saudável
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* GRÁFICO (Ocupa 2 colunas) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-gray-800">Evolução Semestral</h3>
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button 
                onClick={() => setPeriodo('mensal')}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-all ${periodo === 'mensal' ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500'}`}
              >
                Mensal
              </button>
              <button 
                onClick={() => setPeriodo('anual')}
                className={`px-3 py-1 text-xs rounded-md font-medium transition-all ${periodo === 'anual' ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500'}`}
              >
                Anual
              </button>
            </div>
          </div>
          
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} tickFormatter={(value) => `R$${value/1000}k`} />
                <Tooltip 
                  cursor={{fill: '#f3f4f6'}}
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                />
                <Bar dataKey="entrada" name="Entradas" fill="#0ea5e9" radius={[4, 4, 0, 0]} barSize={30} />
                <Bar dataKey="saida" name="Saídas" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={30} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* LISTA DE TRANSAÇÕES RECENTES */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="font-bold text-gray-800 mb-6">Últimos Lançamentos</h3>
          <div className="space-y-4">
            {transactions.map((t) => (
              <div key={t.id} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-xl transition-colors border border-transparent hover:border-gray-100">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    t.tipo === 'entrada' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                  }`}>
                    {t.tipo === 'entrada' ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-800">{t.paciente}</p>
                    <p className="text-xs text-gray-500">{t.proc}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${t.tipo === 'entrada' ? 'text-green-600' : 'text-red-600'}`}>
                    {t.tipo === 'entrada' ? '+' : '-'} R$ {t.valor}
                  </p>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase ${
                    t.status === 'pago' ? 'bg-green-100 text-green-700' :
                    t.status === 'pendente' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {t.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-6 py-2 text-sm text-primary font-medium hover:bg-blue-50 rounded-lg transition-colors">
            Ver Extrato Completo
          </button>
        </div>

      </div>
    </div>
  );
}