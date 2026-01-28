import { useState, useEffect } from 'react';
import { Plus, Trash2, Save, Package, Loader2, CheckCircle2 } from 'lucide-react';

interface InsumoNoProcedimento {
  inventory_item_id: string;
  quantity: number;
}

interface ItemEstoque {
  id: string;
  name: string; // Campo confirmado via inspeção do banco
}

export function ConfigProcedimentos() {
  const [itemsEstoque, setItemsEstoque] = useState<ItemEstoque[]>([]);
  const [nomeProc, setNomeProc] = useState('');
  const [precoProc, setPrecoProc] = useState('');
  const [insumosSelecionados, setInsumosSelecionados] = useState<InsumoNoProcedimento[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    // Busca os itens de estoque populados pelo Seed
    fetch('/api/stock', { 
      headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` } 
    })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setItemsEstoque(data);
      })
      .catch(err => console.error("Erro ao carregar insumos:", err));
  }, []);

  const adicionarInsumo = () => {
    setInsumosSelecionados([...insumosSelecionados, { inventory_item_id: '', quantity: 1 }]);
  };

  const atualizarInsumo = (index: number, campo: keyof InsumoNoProcedimento, valor: string | number) => {
    const novosInsumos = [...insumosSelecionados];
    novosInsumos[index] = { ...novosInsumos[index], [campo]: valor };
    setInsumosSelecionados(novosInsumos);
  };

  const salvarProcedimento = async () => {
    if (!nomeProc || !precoProc) return alert("Preencha o nome e o preço!");
    
    setLoading(true);
    setSuccess(false);

    const payload = {
      name: nomeProc,
      price: parseFloat(precoProc),
      items: insumosSelecionados
    };

    try {
      const res = await fetch('/api/procedures', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
        setNomeProc('');
        setPrecoProc('');
        setInsumosSelecionados([]);
      } else {
        const errorData = await res.json();
        alert(`Erro: ${errorData.error || "Falha ao salvar"}`);
      }
    } catch (error) {
      alert("Erro de conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <div className="max-w-4xl mx-auto bg-white p-10 rounded-[2.5rem] shadow-sm border border-gray-100 animate-in fade-in duration-500">
        <header className="mb-10">
            <h2 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
                <div className="bg-blue-600 p-2 rounded-2xl shadow-lg shadow-blue-100 text-white">
                    <Package size={24}/>
                </div>
                Ficha Técnica de Procedimento
            </h2>
            <p className="text-gray-500 font-medium mt-2">Configure os custos e insumos para baixa automática no estoque.</p>
        </header>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          <div className="space-y-1">
            <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Nome do Procedimento</label>
            <input 
                className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-bold transition-all" 
                placeholder="Ex: Botox 50U ou Clareamento"
                value={nomeProc} onChange={e => setNomeProc(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Preço de Venda (R$)</label>
            <input 
                type="number"
                className="w-full p-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500 font-black text-lg transition-all" 
                placeholder="0,00"
                value={precoProc} onChange={e => setPrecoProc(e.target.value)}
            />
          </div>
        </div>

        <div className="bg-gray-50/50 p-6 rounded-[2rem] border border-gray-100">
            <h3 className="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                Itens Necessários para Execução
            </h3>

            <div className="space-y-3">
                {insumosSelecionados.length === 0 && (
                    <div className="py-10 text-center text-gray-300 border-2 border-dashed border-gray-100 rounded-3xl uppercase text-[10px] font-black tracking-widest">
                        Nenhum insumo adicionado ainda
                    </div>
                )}
                
                {insumosSelecionados.map((insumo, index) => (
                <div key={index} className="flex gap-4 items-center animate-in slide-in-from-left-2">
                    <select 
                        className="flex-1 p-4 bg-white border border-gray-100 rounded-2xl outline-none font-bold text-sm shadow-sm"
                        value={insumo.inventory_item_id}
                        onChange={e => atualizarInsumo(index, 'inventory_item_id', e.target.value)}
                    >
                    <option value="">Selecione o Insumo...</option>
                    {itemsEstoque.map(item => (
                        <option key={item.id} value={item.id}>{item.name}</option>
                    ))}
                    </select>
                    
                    <div className="w-32 flex items-center bg-white border border-gray-100 rounded-2xl px-3 shadow-sm">
                        <input 
                            type="number" 
                            className="w-full p-3 outline-none font-black text-center text-blue-600" 
                            placeholder="Qtd"
                            value={insumo.quantity}
                            onChange={e => atualizarInsumo(index, 'quantity', parseFloat(e.target.value))}
                        />
                    </div>

                    <button 
                        onClick={() => setInsumosSelecionados(insumosSelecionados.filter((_, i) => i !== index))}
                        className="p-4 text-red-400 hover:bg-red-50 hover:text-red-600 rounded-2xl transition-colors"
                    >
                        <Trash2 size={20} />
                    </button>
                </div>
                ))}
            </div>

            <button 
                onClick={adicionarInsumo}
                className="mt-6 w-full py-4 border-2 border-dashed border-blue-100 text-blue-600 rounded-3xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-blue-50 transition-all"
            >
                <Plus size={16}/> Adicionar Material de Consumo
            </button>
        </div>

        <button 
          onClick={salvarProcedimento}
          disabled={loading || success}
          className={`w-full mt-10 p-5 rounded-[1.8rem] font-black text-xs uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all active:scale-95 shadow-xl ${
            success ? 'bg-green-500 text-white' : 'bg-blue-600 text-white shadow-blue-100 hover:bg-blue-700'
          }`}
        >
          {loading ? <Loader2 className="animate-spin" size={20}/> : success ? <CheckCircle2 size={20}/> : <Save size={20}/>}
          {loading ? 'Processando...' : success ? 'Procedimento Configurado!' : 'Salvar Ficha Técnica'}
        </button>
      </div>
    </div>
  );
}