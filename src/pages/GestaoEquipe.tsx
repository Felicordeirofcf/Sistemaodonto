import { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, User, Lock, ArrowUpCircle } from 'lucide-react';

interface Member {
  id: number;
  name: string;
  email: string;
  role: string;
}

export function GestaoEquipe() {
  const [team, setTeam] = useState<Member[]>([]);
  const [limits, setLimits] = useState({ current: 0, max: 0, plan: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Busca a lista de dentistas e os limites do plano da clínica
    const fetchData = async () => {
      try {
        const res = await fetch('/api/clinic/team-stats', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
        });
        const data = await res.json();
        setTeam(data.members);
        setLimits({ 
          current: data.current_count, 
          max: data.max_dentists, 
          plan: data.plan_type 
        });
      } catch (error) {
        console.error("Erro ao carregar equipe", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Gestão da Equipe</h1>
          <p className="text-gray-500">Controle os acessos e profissionais da sua clínica.</p>
        </div>
        
        {/* Indicador de Limite do Plano */}
        <div className="bg-white p-4 rounded-2xl shadow-sm border border-blue-100 flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">Plano {limits.plan}</p>
            <p className="text-sm font-bold text-blue-600">
              {limits.current} / {limits.max} Dentistas
            </p>
          </div>
          <div className="w-12 h-12 rounded-full border-4 border-gray-100 border-t-blue-500 flex items-center justify-center text-xs font-bold text-blue-600">
            {Math.round((limits.current / limits.max) * 100)}%
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LISTA DE MEMBROS */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 text-gray-400 text-xs uppercase font-bold text-left">
              <tr>
                <th className="px-6 py-4">Profissional</th>
                <th className="px-6 py-4">Cargo</th>
                <th className="px-6 py-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {team.map((member) => (
                <tr key={member.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
                        {member.name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-bold text-gray-800">{member.name}</div>
                        <div className="text-xs text-gray-500">{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      member.role === 'admin' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'
                    }`}>
                      {member.role === 'admin' ? 'Administrador' : 'Dentista'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-gray-400 hover:text-red-500 transition-colors">
                      <Lock size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* CARD DE UPGRADE / ADICIONAR */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
              <UserPlus size={20} className="text-blue-500" /> Novo Profissional
            </h3>
            <p className="text-sm text-gray-500 mb-6">
              Adicione dentistas parceiros para que eles gerenciem suas próprias agendas e odontogramas.
            </p>
            
            {limits.current >= limits.max ? (
              <div className="p-4 bg-orange-50 border border-orange-100 rounded-xl">
                <p className="text-xs text-orange-700 font-medium mb-3">
                  Você atingiu o limite do seu plano atual ({limits.plan}).
                </p>
                <button className="w-full py-3 bg-orange-500 text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-orange-600 transition-all">
                  <ArrowUpCircle size={18} /> Fazer Upgrade
                </button>
              </div>
            ) : (
              <button className="w-full py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100">
                Cadastrar Dentista
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}