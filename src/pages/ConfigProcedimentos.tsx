import { useState, useEffect } from 'react';
import { Plus, Trash2, Save, Package } from 'lucide-react';

export function ConfigProcedimentos() {
  const [itemsEstoque, setItemsEstoque] = useState([]);
  const [nomeProc, setNomeProc] = useState('');
  const [precoProc, setPrecoProc] = useState('');
  const [insumosSelecionados, setInsumosSelecionados] = useState([]);

  useEffect(() => {
    // Carrega o estoque para o dentista escolher os insumos
    fetch('/api/stock', { headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` } })
      .then(res => res.json())
      .then(data => setItemsEstoque(data))
      .catch(console.error);
  }, []);

  const adicionarInsumo = () => {
    setInsumosSelecionados([...insumosSelecionados, { inventory_item_id: '', quantity: 1 }]);
  };

  const salvarProcedimento = async () => {
    const payload = {
      name: nomeProc,
      price: parseFloat(precoProc),
      items: insumosSelecionados
    };

    await fetch('/api/procedures', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
      },
      body: JSON.stringify(payload)
    });
    alert("Procedimento salvo! Agora a baixa de estoque será automática.");
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Configurar Novo Procedimento</h2>
        
        <div className="grid grid-cols-2 gap-4 mb-8">
          <input 
            className="p-3 border rounded-xl" 
            placeholder="Nome do Procedimento (Ex: Preenchimento)"
            value={nomeProc} onChange={e => setNomeProc(e.target.value)}
          />
          <input 
            className="p-3 border rounded-xl" 
            placeholder="Preço de Venda (R$)"
            value={precoProc} onChange={e => setPrecoProc(e.target.value)}
          />
        </div>

        <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2">
          <Package size={20} className="text-blue-500"/> Insumos Necessários
        </h3>

        {insumosSelecionados.map((insumo, index) => (
          <div key={index} className="flex gap-4 mb-3 items-center">
            <select 
              className="flex-1 p-2 border rounded-lg"
              onChange={e => {
                const newArr = [...insumosSelecionados];
                newArr[index].inventory_item_id = e.target.value;
                setInsumosSelecionados(newArr);
              }}
            >
              <option value="">Selecione o Insumo...</option>
              {itemsEstoque.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <input 
              type="number" 
              className="w-24 p-2 border rounded-lg" 
              placeholder="Qtd"
              onChange={e => {
                const newArr = [...insumosSelecionados];
                newArr[index].quantity = parseFloat(e.target.value);
                setInsumosSelecionados(newArr);
              }}
            />
            <button onClick={() => setInsumosSelecionados(insumosSelecionados.filter((_, i) => i !== index))}>
              <Trash2 size={18} className="text-red-400" />
            </button>
          </div>
        ))}

        <button 
          onClick={adicionarInsumo}
          className="mt-4 text-sm font-bold text-blue-600 flex items-center gap-1 hover:underline"
        >
          <Plus size={16}/> Adicionar Item (Copo, Agulha, Produto...)
        </button>

        <button 
          onClick={salvarProcedimento}
          className="w-full mt-10 bg-blue-600 text-white p-4 rounded-xl font-bold flex items-center justify-center gap-2"
        >
          <Save size={20}/> Salvar Configuração de Procedimento
        </button>
      </div>
    </div>
  );
}