import { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, User, Lock, ArrowUpCircle, Loader2, X } from 'lucide-react';

interface Member {
  id: number;
  name: string;
  email: string;
  role: string;
}

export function GestaoEquipe() {
  const [team, setTeam] = useState<Member[]>([]);
  const [limits, setLimits] = useState({ current: 0, max: 1, plan: 'Carregando...' });
  const [loading, setLoading] = useState(true);
  
  // Estado para o Modal de Cadastro
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '', role: 'dentist', password: '123' });

  const token = localStorage.getItem('odonto_token');

  const fetchData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const resStats = await fetch('/api/clinic/team-stats', { headers });
      const statsData = await resStats.json();
      
      const resTeam = await fetch('/api/clinic/team', { headers });
      const teamData = await resTeam.json();

      setTeam(Array.isArray(teamData) ? teamData : []);
      setLimits({ 
        current: statsData.dentists_count || 0, 
        max: statsData.max_dentists || 1, 
        plan: statsData.plan_type || 'Bronze' 
      });
    } catch (error) {
      console.error("Erro ao carregar equipe", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreateMember = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch('/api/clinic/team', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify(formData)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || 'Falha ao cadastrar');
      }

      const newMember = await res.json();
      setTeam(prev => [...prev, newMember]);
      setIsModalOpen(false);
      setFormData({ name: '', email: '', role: 'dentist', password: '123' });
      fetchData(); // Atualiza contadores de limite
    } catch (error: any) {
      alert(error.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <Loader2 className="animate-spin text-blue-600" size={48} />
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      {/* HEADER E LIMITES */}
      <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-800 tracking-tight">Gestão da Equipe</h1>
          <p className="text-gray-500 font-medium">Controle os acessos e profissionais da sua clínica.</p>
        </div>
        
        <div className="bg-white p-4 rounded-3xl shadow-sm border border-blue-50 flex items-center gap-4">
          <div className="text-right">
            <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest">Plano {limits.plan}</p>
            <p className="text-sm font-bold text-blue-600">{limits.current} / {limits.max} Dentistas</p>
          </div>
          <div className="w-12 h-12 rounded-full border-4 border-gray-100 border-t-blue-500 flex items-center justify-center text-[10px] font-black text-blue-600">
            {Math.round((limits.current / (limits.max || 1)) * 100)}%
          </div>
        </div>
      </header>

      {/* MODAL DE CADASTRO */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[2.5rem] p-8 max-w-md w-full shadow-2xl animate-in zoom-in duration-200">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-black text-gray-800">Novo Profissional</h2>
              <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleCreateMember} className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Nome Completo</label>
                <input required className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase text-gray-400 ml-1">E-mail (Acesso)</label>
                <input required type="email" className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Cargo</label>
                <select className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
                  <option value="dentist">Dentista</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>
              <button disabled={saving} className="w-full py-4 bg-blue-600 text-white rounded-2xl font-black text-sm uppercase tracking-widest mt-4 flex items-center justify-center gap-2 hover:bg-blue-700 shadow-xl shadow-blue-100">
                {saving ? <Loader2 className="animate-spin" /> : 'Finalizar Cadastro'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* LISTAGEM DE EQUIPE */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50/50 text-gray-400 text-[10px] uppercase font-black text-left">
              <tr>
                <th className="px-6 py-4 tracking-widest">Profissional</th>
                <th className="px-6 py-4 tracking-widest">Cargo</th>
                <th className="px-6 py-4 text-right tracking-widest">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(team || []).map((member) => (
                <tr key={member.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
                        {member.name?.charAt(0) || 'U'}
                      </div>
                      <div>
                        <div className="font-bold text-gray-800 text-sm">{member.name}</div>
                        <div className="text-[11px] text-gray-400">{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-tighter ${
                      member.role === 'admin' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'
                    }`}>
                      {member.role === 'admin' ? 'Administrador' : 'Dentista'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 transition-all rounded-lg">
                      <Lock size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* CARD DE AÇÃO */}
        <div className="space-y-6">
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 mb-6"><UserPlus size={24} /></div>
            <h3 className="font-bold text-gray-800 mb-2 text-lg">Novo Profissional</h3>
            <p className="text-xs text-gray-500 mb-8 leading-relaxed font-medium">Adicione dentistas para gerenciarem suas próprias agendas e pacientes.</p>
            
            {limits.current >= limits.max ? (
              <div className="p-5 bg-orange-50 border border-orange-100 rounded-2xl">
                <p className="text-[11px] text-orange-700 font-bold mb-4">Limite atingido para o plano {limits.plan}.</p>
                <button className="w-full py-3 bg-orange-500 text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-orange-600 shadow-lg shadow-orange-100"><ArrowUpCircle size={18} /> Fazer Upgrade</button>
              </div>
            ) : (
              <button onClick={() => setIsModalOpen(true)} className="w-full py-4 bg-blue-600 text-white rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-blue-700 shadow-xl shadow-blue-100 transition-all flex items-center justify-center gap-2 active:scale-95"><UserPlus size={20} /> Cadastrar Dentista</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}