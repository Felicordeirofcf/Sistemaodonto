import { useState, useEffect } from 'react';
import { Search, Plus, Phone, FileText, User, X, Loader2 } from 'lucide-react';

// Interface ajustada para bater com o Python (name ao invés de nome)
interface Paciente {
  id: number;
  name: string;      // Python envia "name"
  cpf?: string;
  phone: string;     // Python envia "phone"
  email?: string;
  address?: string;
  status?: string;   // Opcional, caso não venha do back
}

export function Pacientes() {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Estado do formulário
  const [novoPaciente, setNovoPaciente] = useState({ 
    name: '', 
    cpf: '', 
    phone: '', 
    email: '',
    address: ''
  });

  const getToken = () => localStorage.getItem('odonto_token');

  const carregarPacientes = async () => {
    setLoading(true);
    const token = getToken();
    try {
      const res = await fetch('/api/patients', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) {
        throw new Error(`Erro API: ${res.status}`);
      }

      const data = await res.json();
      // Garante que é um array antes de setar
      if (Array.isArray(data)) {
        setPacientes(data);
      } else {
        console.error("Formato inválido recebido:", data);
        setPacientes([]);
      }
    } catch (error) {
      console.error("Falha ao buscar pacientes:", error);
      // Não trava a tela, apenas deixa lista vazia
      setPacientes([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarPacientes();
  }, []);

  const handleSalvar = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();
    
    try {
      const response = await fetch('/api/patients', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(novoPaciente)
      });

      if (response.ok) {
        alert('Paciente cadastrado com sucesso!');
        setIsModalOpen(false);
        setNovoPaciente({ name: '', cpf: '', phone: '', email: '', address: '' });
        carregarPacientes();
      } else {
        const err = await response.json();
        alert(`Erro: ${err.error || 'Falha ao salvar'}`);
      }
    } catch (error) {
      alert('Erro de conexão ao tentar salvar.');
    }
  };

  // Filtragem segura (verifica se p.name existe antes de dar toLowerCase)
  const pacientesFiltrados = pacientes.filter(p => 
    (p.name && p.name.toLowerCase().includes(busca.toLowerCase())) || 
    (p.cpf && p.cpf.includes(busca))
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen font-sans relative">
      {/* MODAL DE CADASTRO */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-md animate-in zoom-in-95">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-800">Novo Paciente</h2>
              <button onClick={() => setIsModalOpen(false)}><X size={24} className="text-gray-400 hover:text-red-500"/></button>
            </div>
            
            <form onSubmit={handleSalvar} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Nome Completo *</label>
                <input required className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                  value={novoPaciente.name} onChange={e => setNovoPaciente({...novoPaciente, name: e.target.value})} />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                   <label className="text-sm font-medium text-gray-700">CPF</label>
                   <input className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                     value={novoPaciente.cpf} onChange={e => setNovoPaciente({...novoPaciente, cpf: e.target.value})} />
                </div>
                <div>
                   <label className="text-sm font-medium text-gray-700">Telefone *</label>
                   <input required className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                     value={novoPaciente.phone} onChange={e => setNovoPaciente({...novoPaciente, phone: e.target.value})} />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700">Email</label>
                <input type="email" className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                  value={novoPaciente.email} onChange={e => setNovoPaciente({...novoPaciente, email: e.target.value})} />
              </div>

              <button type="submit" className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg mt-4 hover:bg-blue-700 transition-colors">
                Salvar Cadastro
              </button>
            </form>
          </div>
        </div>
      )}

      {/* CABEÇALHO */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gestão de Pacientes</h1>
          <p className="text-gray-500 text-sm">Gerencie cadastros reais do sistema.</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg flex items-center gap-2 font-semibold shadow-sm transition-all">
          <Plus size={20} /> Novo Paciente
        </button>
      </div>

      {/* BARRA DE BUSCA */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex items-center gap-3">
        <Search className="text-gray-400" size={20} />
        <input type="text" placeholder="Buscar por nome ou CPF..." className="flex-1 outline-none text-gray-700 placeholder-gray-400" value={busca} onChange={(e) => setBusca(e.target.value)} />
      </div>

      {/* TABELA DE DADOS */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[300px]">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Loader2 className="animate-spin mb-2" size={32} />
            <p>Carregando pacientes...</p>
          </div>
        ) : pacientesFiltrados.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                <User size={48} className="mb-2 opacity-20" />
                <p>Nenhum paciente encontrado.</p>
            </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="p-4 text-xs font-bold text-gray-500 uppercase">Paciente</th>
                  <th className="p-4 text-xs font-bold text-gray-500 uppercase hidden md:table-cell">CPF</th>
                  <th className="p-4 text-xs font-bold text-gray-500 uppercase">Contato</th>
                  <th className="p-4 text-xs font-bold text-gray-500 uppercase text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {pacientesFiltrados.map((paciente) => (
                  <tr key={paciente.id} className="hover:bg-gray-50 transition-colors">
                    <td className="p-4 flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold shrink-0">
                            {paciente.name ? paciente.name.charAt(0).toUpperCase() : '?'}
                        </div>
                        <div>
                            <span className="font-semibold text-gray-800 block">{paciente.name}</span>
                            <span className="text-xs text-gray-400">{paciente.email}</span>
                        </div>
                    </td>
                    <td className="p-4 text-sm text-gray-600 hidden md:table-cell">{paciente.cpf || '-'}</td>
                    <td className="p-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                            <Phone size={14} className="text-gray-400"/> 
                            {paciente.phone}
                        </div>
                    </td>
                    <td className="p-4 text-right">
                        <button className="text-gray-400 hover:text-blue-600 p-2" title="Ver Prontuário">
                            <FileText size={18} />
                        </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}