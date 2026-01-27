import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, TrendingDown, Filter, Download } from 'lucide-react';

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
  const [balance, setBalance] = useState(0);

  useEffect(() => {
    fetch('/api/financial/transactions', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
      .then(res => res.json())
      .then(data => {
          if(data.transactions) {
              setTransactions(data.transactions);
              setBalance(data.balance);
          }
      })
      .catch(console.error);
  }, []);

  return (
    <div className="p-8 w-full bg-gray-50 min-h-screen">
      <header className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Financeiro</h1>
          <p className="text-gray-500 mt-1">Fluxo de caixa em tempo real</p>
        </div>
        <div className="text-right">
            <p className="text-sm text-gray-500 mb-1">Saldo Atual</p>
            <h2 className={`text-4xl font-bold ${balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                R$ {balance.toFixed(2)}
            </h2>
        </div>
      </header>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
            <h3 className="font-bold text-gray-700">Histórico de Transações</h3>
            <button className="flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600"><Download size={16}/> Exportar</button>
        </div>
        
        <table className="w-full">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase font-semibold text-left">
            <tr>
              <th className="px-6 py-4">Descrição</th>
              <th className="px-6 py-4">Categoria</th>
              <th className="px-6 py-4">Data</th>
              <th className="px-6 py-4 text-right">Valor</th>
              <th className="px-6 py-4 text-center">Tipo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {transactions.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-10 text-gray-400">Nenhuma transação encontrada. Finalize uma consulta na Agenda.</td></tr>
            ) : (
                transactions.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-800">{t.description}</td>
                    <td className="px-6 py-4 text-sm text-gray-500"><span className="bg-gray-100 px-2 py-1 rounded text-xs font-bold">{t.category}</span></td>
                    <td className="px-6 py-4 text-sm text-gray-500">{new Date(t.date).toLocaleDateString()}</td>
                    <td className={`px-6 py-4 text-right font-bold ${t.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                    R$ {t.amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-center">
                        {t.type === 'income' ? <TrendingUp size={16} className="text-green-500 inline"/> : <TrendingDown size={16} className="text-red-500 inline"/>}
                    </td>
                </tr>
                ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}