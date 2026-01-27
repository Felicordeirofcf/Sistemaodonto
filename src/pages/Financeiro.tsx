import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, TrendingDown, Plus, Wallet, ArrowDownCircle } from 'lucide-react';

interface Transaction {
  id: number;
  description: string;
  amount: number;
  type: 'income' | 'expense';
  category: string;
  date: string;
}

export function Financeiro() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState({ receita: 0, despesas: 0, lucro: 0 });
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Estado para Nova Despesa
  const [newExpense, setNewExpense] = useState({ description: '', amount: '', category: 'Despesa Fixa' });

  const loadData = () => {
    fetch('/api/financial/summary', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
      .then(res => res.json())
      .then(data => {
          setSummary({ receita: data.receita, despesas: data.despesas, lucro: data.lucro });
          setTransactions(data.transactions);
      })
      .catch(console.error);
  };

  useEffect(() => { loadData(); }, []);

  const handleSaveExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/financial/expense', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        },
        body: JSON.stringify(newExpense)
    });
    setIsModalOpen(false);
    setNewExpense({ description: '', amount: '', category: 'Despesa Fixa' });
    loadData(); // Recarrega os dados
  };

  const Card = ({ title, value, color, icon: Icon }: any) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
        <div className={`p-4 rounded-full ${color} bg-opacity-10 text-${color.split('-')[1]}-600`}>
            <Icon size={24} className={color.replace('bg-', 'text-').replace('-100', '-600')} />
        </div>
        <div>
            <p className="text-sm text-gray-500 font-medium">{title}</p>
            <h3 className={`text-2xl font-bold ${color.replace('bg-', 'text-').replace('-100', '-700')}`}>
                R$ {value.toFixed(2)}
            </h3>
        </div>
    </div>
  );

  return (
    <div className="p-8 w-full bg-gray-50 min-h-screen relative">
      <header className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Gestão Financeira</h1>
          <p className="text-gray-500">Controle de lucro e despesas.</p>
        </div>
        <button 
            onClick={() => setIsModalOpen(true)}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 shadow-lg shadow-red-200 transition-all"
        >
            <ArrowDownCircle size={20} /> Lançar Despesa
        </button>
      </header>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card title="Receita Total" value={summary.receita} color="bg-green-100" icon={TrendingUp} />
        <Card title="Despesas" value={summary.despesas} color="bg-red-100" icon={TrendingDown} />
        <Card title="Lucro Líquido" value={summary.lucro} color="bg-blue-100" icon={Wallet} />
      </div>

      {/* TABELA */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50/50">
            <h3 className="font-bold text-gray-700">Extrato Recente</h3>
        </div>
        <table className="w-full">
          <thead className="bg-white text-gray-500 text-xs uppercase font-semibold text-left">
            <tr>
              <th className="px-6 py-4">Descrição</th>
              <th className="px-6 py-4">Categoria</th>
              <th className="px-6 py-4">Data</th>
              <th className="px-6 py-4 text-right">Valor</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {transactions.length === 0 ? (
                <tr><td colSpan={4} className="text-center py-8 text-gray-400">Nenhum lançamento ainda.</td></tr>
            ) : transactions.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-800">{t.description}</td>
                    <td className="px-6 py-4"><span className="bg-gray-100 px-2 py-1 rounded text-xs font-bold text-gray-600">{t.category}</span></td>
                    <td className="px-6 py-4 text-sm text-gray-500">{new Date(t.date).toLocaleDateString()}</td>
                    <td className={`px-6 py-4 text-right font-bold ${t.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                        {t.type === 'expense' ? '- ' : '+ '} R$ {t.amount.toFixed(2)}
                    </td>
                </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* MODAL DE DESPESA */}
      {isModalOpen && (
          <div className="absolute inset-0 z-50 bg-black/50 flex items-center justify-center backdrop-blur-sm fixed">
              <div className="bg-white p-6 rounded-xl shadow-2xl w-96">
                  <h3 className="text-lg font-bold mb-4 text-gray-800">Lançar Saída / Despesa</h3>
                  <form onSubmit={handleSaveExpense} className="flex flex-col gap-3">
                      <input required placeholder="Descrição (Ex: Aluguel)" className="p-2 border rounded" value={newExpense.description} onChange={e => setNewExpense({...newExpense, description: e.target.value})} />
                      <input required type="number" placeholder="Valor (R$)" className="p-2 border rounded" value={newExpense.amount} onChange={e => setNewExpense({...newExpense, amount: e.target.value})} />
                      <select className="p-2 border rounded" value={newExpense.category} onChange={e => setNewExpense({...newExpense, category: e.target.value})}>
                          <option>Despesa Fixa</option>
                          <option>Material</option>
                          <option>Impostos</option>
                          <option>Comissão</option>
                          <option>Outros</option>
                      </select>
                      <div className="flex gap-2 mt-2">
                          <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 bg-gray-200 text-gray-700 p-2 rounded font-bold">Cancelar</button>
                          <button type="submit" className="flex-1 bg-red-600 text-white p-2 rounded font-bold">Salvar Saída</button>
                      </div>
                  </form>
              </div>
          </div>
      )}
    </div>
  );
}