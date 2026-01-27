import { useState, useEffect } from 'react';
import { Package, Plus, Minus, AlertTriangle, Search, Filter, X } from 'lucide-react';

interface ItemEstoque {
  id: number;
  nome: string;
  categoria: string;
  quantidade: number;
  minimo: number;
  unidade: string;
}

export function Estoque() {
  const [itens, setItens] = useState<ItemEstoque[]>([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  
  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [novoItem, setNovoItem] = useState({ 
    nome: '', categoria: 'Material', quantidade: 0, minimo: 5, unidade: 'un' 
  });

  // 1. CARREGAR DADOS
  const carregarEstoque = () => {
    fetch('http://127.0.0.1:5000/api/stock')
      .then(res => res.json())
      .then(data => {
        setItens(data);
        setLoading(false);
      });
  };

  useEffect(() => {
    carregarEstoque();
  }, []);

  // 2. ATUALIZAR QUANTIDADE (+ ou -)
  const ajustarEstoque = async (id: number, delta: number) => {
    // Atualiza visualmente na hora (Otimista)
    setItens(prev => prev.map(item => {
      if (item.id === id) {
        return { ...item, quantidade: Math.max(0, item.quantidade + delta) };
      }
      return item;
    }));

    // Envia para o servidor
    await fetch(`http://127.0.0.1:5000/api/stock/${id}/update`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta })
    });
  };

  // 3. SALVAR NOVO ITEM
  const handleSalvar = async (e: React.FormEvent) => {
    e.preventDefault();
    const response = await fetch('http://127.0.0.1:5000/api/stock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(novoItem)
    });

    if (response.ok) {
      alert('Item adicionado!');
      setIsModalOpen(false);
      setNovoItem({ nome: '', categoria: 'Material', quantidade: 0, minimo: 5, unidade: 'un' });
      carregarEstoque();
    }
  };

  const itensFiltrados = itens.filter(i => i.nome.toLowerCase().includes(busca.toLowerCase()));
  const itensCriticos = itens.filter(i => i.quantidade <= i.minimo).length;

  return (
    <div className="p-6 bg-gray-50 min-h-screen font-sans relative">
      
      {/* MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-md animate-in zoom-in-95">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Novo Material</h2>
              <button onClick={() => setIsModalOpen(false)}><X className="text-gray-400 hover:text-red-500"/></button>
            </div>
            <form onSubmit={handleSalvar} className="space-y-3">
              <input required placeholder="Nome do Item" className="w-full p-2 border rounded" value={novoItem.nome} onChange={e => setNovoItem({...novoItem, nome: e.target.value})} />
              <div className="flex gap-2">
                <select className="p-2 border rounded flex-1" value={novoItem.categoria} onChange={e => setNovoItem({...novoItem, categoria: e.target.value})}>
                  <option>Material</option>
                  <option>Medicamento</option>
                  <option>Descartável</option>
                  <option>Instrumental</option>
                </select>
                <input placeholder="Unid (ex: cx)" className="w-20 p-2 border rounded" value={novoItem.unidade} onChange={e => setNovoItem({...novoItem, unidade: e.target.value})} />
              </div>
              <div className="flex gap-2">
                <div className="flex-1">
                  <label className="text-xs text-gray-500">Qtd Inicial</label>
                  <input type="number" className="w-full p-2 border rounded" value={novoItem.quantidade} onChange={e => setNovoItem({...novoItem, quantidade: parseInt(e.target.value)})} />
                </div>
                <div className="flex-1">
                  <label className="text-xs text-gray-500">Mínimo (Alerta)</label>
                  <input type="number" className="w-full p-2 border rounded" value={novoItem.minimo} onChange={e => setNovoItem({...novoItem, minimo: parseInt(e.target.value)})} />
                </div>
              </div>
              <button className="w-full bg-indigo-600 text-white py-2 rounded font-bold hover:bg-indigo-700">Salvar Item</button>
            </form>
          </div>
        </div>
      )}

      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Controle de Estoque</h1>
          <p className="text-gray-500 text-sm">Gerencie insumos e evite falta de material.</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg flex items-center gap-2 font-semibold shadow-sm transition-all">
          <Plus size={20} /> Novo Item
        </button>
      </div>

      {/* CARD DE ALERTA */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
        <div className={`border p-4 rounded-xl flex items-center gap-4 transition-all ${itensCriticos > 0 ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'}`}>
          <div className={`p-3 rounded-full ${itensCriticos > 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <h3 className={`text-lg font-bold ${itensCriticos > 0 ? 'text-red-800' : 'text-green-800'}`}>
              {itensCriticos} Itens
            </h3>
            <p className="text-sm text-gray-600">{itensCriticos > 0 ? 'Com estoque crítico' : 'Tudo sob controle'}</p>
          </div>
        </div>
      </div>

      {/* TABELA */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex gap-4 bg-gray-50/50">
          <div className="flex-1 flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-gray-200">
            <Search size={18} className="text-gray-400"/>
            <input type="text" placeholder="Buscar material..." className="flex-1 outline-none text-sm" value={busca} onChange={e => setBusca(e.target.value)} />
          </div>
        </div>

        {loading ? <div className="p-8 text-center text-gray-400">Carregando estoque...</div> : (
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="p-4 text-xs font-bold text-gray-500 uppercase">Item</th>
              <th className="p-4 text-xs font-bold text-gray-500 uppercase">Categoria</th>
              <th className="p-4 text-xs font-bold text-gray-500 uppercase text-center">Quantidade</th>
              <th className="p-4 text-xs font-bold text-gray-500 uppercase text-center">Status</th>
              <th className="p-4 text-xs font-bold text-gray-500 uppercase text-right">Ajuste</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {itensFiltrados.map((item) => {
              const isLow = item.quantidade <= item.minimo;
              return (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg text-gray-500"><Package size={18} /></div>
                      <div>
                        <p className="font-semibold text-gray-800 text-sm">{item.nome}</p>
                        <p className="text-xs text-gray-400">{item.unidade}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-sm text-gray-600">
                    <span className="px-2 py-1 bg-gray-100 rounded-md text-xs font-medium text-gray-600 border border-gray-200">{item.categoria}</span>
                  </td>
                  <td className="p-4 text-center">
                    <span className={`text-lg font-bold ${isLow ? 'text-red-600' : 'text-gray-800'}`}>{item.quantidade}</span>
                  </td>
                  <td className="p-4 text-center">
                    {isLow ? 
                      <span className="px-2 py-1 rounded-full text-[10px] font-bold uppercase bg-red-100 text-red-700">Baixo</span> : 
                      <span className="px-2 py-1 rounded-full text-[10px] font-bold uppercase bg-green-100 text-green-700">OK</span>
                    }
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => ajustarEstoque(item.id, -1)} className="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors"><Minus size={14} /></button>
                      <button onClick={() => ajustarEstoque(item.id, 1)} className="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 hover:bg-green-50 hover:text-green-600 hover:border-green-200 transition-colors"><Plus size={14} /></button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        )}
      </div>
    </div>
  );
}