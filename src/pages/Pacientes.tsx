import { useState, useEffect } from 'react';
import { Search, Plus, Phone, Calendar, FileText, User, X } from 'lucide-react';

interface Paciente {
  id: number;
  nome: string;
  cpf: string;
  telefone: string;
  ultimaConsulta: string;
  status: 'ativo' | 'inativo';
}

export function Pacientes() {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [novoPaciente, setNovoPaciente] = useState({ nome: '', cpf: '', telefone: '' });

  // Função auxiliar para pegar token
  const getToken = () => localStorage.getItem('odonto_token');

  const carregarPacientes = () => {
    const token = getToken();
    fetch('http://127.0.0.1:5000/api/patients', {
        headers: { 'Authorization': `Bearer ${token}` } // TOKEN AQUI
    })
      .then(res => {
          if (res.status === 401) return []; 
          return res.json();
      })
      .then(data => {
        setPacientes(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    carregarPacientes();
  }, []);

  const handleSalvar = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = getToken();
    
    const response = await fetch('http://127.0.0.1:5000/api/patients', {
      method: 'POST',
      headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // TOKEN AQUI
      },
      body: JSON.stringify(novoPaciente)
    });

    if (response.ok) {
      alert('Paciente cadastrado!');
      setIsModalOpen(false);
      setNovoPaciente({ nome: '', cpf: '', telefone: '' });
      carregarPacientes();
    } else {
      alert('Erro ao cadastrar.');
    }
  };

  const pacientesFiltrados = pacientes.filter(p => 
    p.nome.toLowerCase().includes(busca.toLowerCase()) || 
    p.cpf.includes(busca)
  );

  return (
    <div className="p-6 bg-gray-50 min-h-screen font-sans relative">
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-md animate-in zoom-in-95">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-gray-800">Novo Paciente</h2>
              <button onClick={() => setIsModalOpen(false)}><X size={24} className="text-gray-400"/></button>
            </div>
            <form onSubmit={handleSalvar} className="space-y-4">
              <input required placeholder="Nome Completo" className="w-full p-2 border rounded-lg" value={novoPaciente.nome} onChange={e => setNovoPaciente({...novoPaciente, nome: e.target.value})} />
              <input placeholder="CPF" className="w-full p-2 border rounded-lg" value={novoPaciente.cpf} onChange={e => setNovoPaciente({...novoPaciente, cpf: e.target.value})} />
              <input placeholder="Telefone" className="w-full p-2 border rounded-lg" value={novoPaciente.telefone} onChange={e => setNovoPaciente({...novoPaciente, telefone: e.target.value})} />
              <button type="submit" className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg mt-4">Salvar Cadastro</button>
            </form>
          </div>
        </div>
      )}

      <div className="flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gestão de Pacientes</h1>
          <p className="text-gray-500 text-sm">Gerencie cadastros reais do sistema.</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="bg-blue-600 text-white px-5 py-2.5 rounded-lg flex items-center gap-2 font-semibold shadow-sm">
          <Plus size={20} /> Novo Paciente
        </button>
      </div>

      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex items-center gap-3">
        <Search className="text-gray-400" size={20} />
        <input type="text" placeholder="Buscar..." className="flex-1 outline-none" value={busca} onChange={(e) => setBusca(e.target.value)} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[300px]">
        {loading ? <div className="p-10 text-center text-gray-400">Carregando...</div> : (
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="p-4 text-xs font-bold text-gray-500 uppercase">Paciente</th>
                <th className="p-4 text-xs font-bold text-gray-500 uppercase hidden md:table-cell">CPF</th>
                <th className="p-4 text-xs font-bold text-gray-500 uppercase">Contato</th>
                <th className="p-4 text-xs font-bold text-gray-500 uppercase">Status</th>
                <th className="p-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {pacientesFiltrados.map((paciente) => (
                <tr key={paciente.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold"><User size={14} /></div>
                      <span className="font-semibold text-gray-800">{paciente.nome}</span>
                  </td>
                  <td className="p-4 text-sm text-gray-600 hidden md:table-cell">{paciente.cpf}</td>
                  <td className="p-4 text-sm text-gray-600"><Phone size={14} className="inline mr-1 text-gray-400"/> {paciente.telefone}</td>
                  <td className="p-4"><span className="px-2 py-1 rounded-full text-xs font-bold bg-green-100 text-green-700">{paciente.status || 'Ativo'}</span></td>
                  <td className="p-4 text-right"><button className="text-gray-400 hover:text-blue-600"><FileText size={18} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}