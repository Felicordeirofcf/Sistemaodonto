import { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, User, Lock, ArrowUpCircle, Loader2 } from 'lucide-react';

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

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('odonto_token');
        // Chamada para a nova rota de estatísticas que criamos no backend
        const res = await fetch('/api/clinic/team-stats', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!res.ok) throw new Error('Falha ao carregar dados');
        
        const data = await res.json();
        
        // Chamada para listar os membros reais da clínica
        const resTeam = await fetch('/api/clinic/team', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const teamData = await resTeam.json();

        setTeam(teamData || []); // Blindagem contra null/undefined
        setLimits({ 
          current: data.dentists_count || 0, 
          max: data.max_dentists || 1, 
          plan: data.plan_type || 'Bronze' 
        });
      } catch (error) {
        console.error("Erro ao carregar equipe", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <Loader2 className="animate-spin text-blue-600" size={48} />
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 tracking-tight">Gestão da Equipe</h1>
          <p className="text-gray-500">Controle os acessos e profissionais da sua clínica.</p>
        </div>
        
        <div className="bg-white p-4 rounded-3xl shadow-sm border border-blue-50 flex items-center gap-4">
          <div className="text-right">
            <p className="text-[10px] text-gray-400 uppercase font-black tracking-widest">Plano {limits.plan}</p>
            <p className="text-sm font-bold text-blue-600">
              {limits.current} / {limits.max} Dentistas
            </p>
          </div>
          <div className="w-12 h-12 rounded-full border-4 border-gray-100 border-t-blue-500 flex items-center justify-center text-[10px] font-black text-blue-600">
            {Math.round((limits.current / (limits.max || 1)) * 100)}%
          </div>
        </div>
      </header>

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
              {/* Uso de fallback array para evitar erros de map */}
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

        <div className="space-y-6">
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
            <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 mb-6">
              <UserPlus size={24} />
            </div>
            <h3 className="font-bold text-gray-800 mb-2">Novo Profissional</h3>
            <p className="text-xs text-gray-500 mb-8 leading-relaxed">
              Adicione dentistas parceiros para que eles gerenciem suas próprias agendas e odontogramas.
            </p>
            
            {limits.current >= limits.max ? (
              <div className="p-5 bg-orange-50 border border-orange-100 rounded-2xl">
                <p className="text-[11px] text-orange-700 font-bold mb-4">
                  Limite atingido para o plano {limits.plan}.
                </p>
                <button className="w-full py-3 bg-orange-500 text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-orange-600 transition-all shadow-lg shadow-orange-200">
                  <ArrowUpCircle size={18} /> Fazer Upgrade
                </button>
              </div>
            ) : (
              <button className="w-full py-4 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 transition-all shadow-xl shadow-blue-100 flex items-center justify-center gap-2">
                <UserPlus size={20} /> Cadastrar Dentista
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}