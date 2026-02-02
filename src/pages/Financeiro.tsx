import { useState, useEffect } from 'react';
import { 
  DollarSign, TrendingUp, TrendingDown, Plus, Wallet, 
  ArrowDownCircle, ArrowUpCircle, X, Loader2 
} from 'lucide-react';

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
  const [loading, setLoading] = useState(true);
  
  // Estado Unificado para Lançamento
  const [newEntry, setNewEntry] = useState({ 
    description: '', 
    amount: '', 
    category: 'Procedimento', 
    type: 'income' as 'income' | 'expense' 
  });

  const loadData = async () => {
    try {
      const res = await fetch('/api/financial/summary', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
      });
      const data = await res.json();
      setSummary({ receita: data.receita || 0, despesas: data.despesas || 0, lucro: data.lucro || 0 });
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error("Erro financeiro:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleSaveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    // Rota genérica de transação para suportar ambos os tipos
    await fetch('/api/financial/transaction', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
      },
      body: JSON.stringify(newEntry)
    });
    setIsModalOpen(false);
    setNewEntry({ description: '', amount: '', category: 'Procedimento', type: 'income' });
    loadData();
  };

  const Card = ({ title, value, color, icon: Icon }: any) => (
    <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-gray-100 flex items-center gap-6 group hover:shadow-xl transition-all">
      <div className={`p-5 rounded-2xl ${color} bg-opacity-10 transition-transform group-hover:scale-110`}>
        <Icon size={32} className={color.replace('bg-', 'text-').replace('-100', '-600')} />
      </div>
      <div>
        <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest mb-1">{title}</p>
        <h3 className={`text-2xl font-black tracking-tighter ${color.replace('bg-', 'text-').replace('-100', '-700')}`}>
          {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)}
        </h3>
      </div>
    </div>
  );

  if (loading) return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <Loader2 className="animate-spin text-blue-600" size={48} />
    </div>
  );

  return (
    <div className="p-8 w-full bg-gray-50 min-h-screen relative font-sans">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-10 gap-4">
        <div>
          <h1 className="text-4xl font-black text-gray-900 tracking-tight">Gestão Financeira</h1>
          <p className="text-gray-500 font-medium">Controle total de fluxo de caixa e rentabilidade.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-blue-600 text-white px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-3 shadow-xl shadow-blue-100 hover:bg-blue-700 transition-all active:scale-95"
        >
          <Plus size={20} /> Novo Lançamento
        </button>
      </header>

      {/* KPI CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
        <Card title="Receita Bruta" value={summary.receita} color="bg-green-100" icon={TrendingUp} />
        <Card title="Custos / Despesas" value={summary.despesas} color="bg-red-100" icon={TrendingDown} />
        <Card title="Lucro Líquido" value={summary.lucro} color="bg-blue-100" icon={Wallet} />
      </div>

      {/* TABELA PREMIUM */}
      <div className="bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-8 border-b border-gray-50 bg-gray-50/30">
          <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">Extrato de Movimentações</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-[10px] font-black text-gray-400 uppercase tracking-widest border-b border-gray-50">
                <th className="px-8 py-5">Descrição</th>
                <th className="px-8 py-5">Categoria</th>
                <th className="px-8 py-5">Data</th>
                <th className="px-8 py-5 text-right">Valor</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 font-bold">
              {transactions.length === 0 ? (
                <tr><td colSpan={4} className="text-center py-20 text-gray-300 uppercase text-xs tracking-widest">Nenhum registro encontrado</td></tr>
              ) : transactions.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50/50 transition-colors group">
                  <td className="px-8 py-6 text-gray-800">{t.description}</td>
                  <td className="px-8 py-6">
                    <span className="bg-gray-100 px-3 py-1.5 rounded-xl text-[9px] font-black uppercase text-gray-500 tracking-tighter">
                      {t.category}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-xs text-gray-400">{new Date(t.date).toLocaleDateString('pt-BR')}</td>
                  <td className={`px-8 py-6 text-right text-sm ${t.type === 'income' ? 'text-green-600' : 'text-red-500'}`}>
                    {t.type === 'expense' ? '- ' : '+ '} 
                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(t.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL DE LANÇAMENTO UNIFICADO */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white p-8 rounded-[2.5rem] shadow-2xl w-full max-w-md animate-in zoom-in duration-200">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-2xl font-black text-gray-800 tracking-tight">Novo Registro</h3>
              <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-400">
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSaveEntry} className="flex flex-col gap-6">
              {/* Seletor de Tipo Receita/Despesa */}
              <div className="flex bg-gray-100 p-1.5 rounded-2xl gap-2">
                <button 
                  type="button"
                  onClick={() => setNewEntry({...newEntry, type: 'income', category: 'Procedimento'})}
                  className={`flex-1 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${newEntry.type === 'income' ? 'bg-green-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-600'}`}
                >
                  <ArrowUpCircle size={14} className="inline mr-2" /> Receita
                </button>
                <button 
                  type="button"
                  onClick={() => setNewEntry({...newEntry, type: 'expense', category: 'Material'})}
                  className={`flex-1 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all ${newEntry.type === 'expense' ? 'bg-red-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-600'}`}
                >
                  <ArrowDownCircle size={14} className="inline mr-2" /> Despesa
                </button>
              </div>

              <div className="space-y-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Descrição</label>
                  <input required placeholder="Ex: Limpeza Dental ou Aluguel" className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-bold" value={newEntry.description} onChange={e => setNewEntry({...newEntry, description: e.target.value})} />
                </div>
                
                <div className="space-y-1">
                  <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Valor (R$)</label>
                  <input required type="number" step="0.01" placeholder="0,00" className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-black text-lg" value={newEntry.amount} onChange={e => setNewEntry({...newEntry, amount: e.target.value})} />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Categoria</label>
                  <select className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none appearance-none font-bold" value={newEntry.category} onChange={e => setNewEntry({...newEntry, category: e.target.value})}>
                    {newEntry.type === 'income' ? (
                      <>
                        <option>Procedimento</option>
                        <option>Venda de Produto</option>
                        <option>Consultoria</option>
                        <option>Outros</option>
                      </>
                    ) : (
                      <>
                        <option>Material</option>
                        <option>Aluguel / Fixos</option>
                        <option>Impostos</option>
                        <option>Comissão</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              <button 
                type="submit" 
                className={`w-full py-5 rounded-2xl font-black uppercase text-xs tracking-[0.2em] shadow-xl transition-all active:scale-95 text-white ${newEntry.type === 'income' ? 'bg-green-600 shadow-green-100' : 'bg-red-600 shadow-red-100'}`}
              >
                Confirmar Lançamento
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}