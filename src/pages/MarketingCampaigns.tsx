import { useState, useEffect } from 'react';
import { MessageSquare, Zap, AlertCircle } from 'lucide-react';

// 1. Definição da Interface para o Paciente do Recall
interface RecallPatient {
  id: number;
  name: string;
  phone: string;
  last_visit: string;
  suggested_msg: string;
}

export function MarketingCampaigns() {
  // 2. Tipagem explícita do State para evitar erro de .map()
  const [candidates, setCandidates] = useState<RecallPatient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetch('/api/marketing/campaign/recall', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
    .then(res => {
      if (!res.ok) throw new Error('Falha na API');
      return res.json();
    })
    .then(data => {
      // 3. Verificação de segurança: garante que data é um Array antes de salvar
      if (Array.isArray(data)) {
        setCandidates(data);
      } else {
        setCandidates([]);
      }
    })
    .catch((err) => {
      console.error(err);
      setError(true);
      setCandidates([]); // Fallback para array vazio evita que o .map quebre
    })
    .finally(() => setLoading(false));
  }, []);

  const triggerBot = (patient: RecallPatient) => {
    // 4. Usa a mensagem personalizada que vem da IA no Backend
    const whatsappUrl = `https://wa.me/${patient.phone}?text=${encodeURIComponent(patient.suggested_msg)}`;
    window.open(whatsappUrl, '_blank');
  };

  if (loading) return <div className="p-8 text-gray-500 animate-pulse">Carregando candidatos...</div>;

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Automação de Vendas</h1>
        <p className="text-gray-500">O robô identifica pacientes sumidos e sugere horários na agenda.</p>
      </header>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl flex items-center gap-2">
          <AlertCircle size={20} />
          <span>Erro ao conectar com o servidor de campanhas. Verifique as rotas do backend.</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* CARD DE STATUS DO ROBÔ */}
        <div className="lg:col-span-1 bg-white p-6 rounded-2xl shadow-sm border border-blue-100 h-fit">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-blue-100 text-blue-600 rounded-xl"><Zap size={24}/></div>
            <h2 className="font-bold text-lg">Status do Bot</h2>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Pacientes para Recuperar:</span>
              <span className="font-bold text-blue-600">{candidates.length}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Vagas na Agenda (Amanhã):</span>
              <span className="font-bold text-green-600">Disponíveis</span>
            </div>
            <button className="w-full py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all">
              Ativar Disparo Automático
            </button>
          </div>
        </div>

        {/* LISTA DE CANDIDATOS AO RECALL */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-50 bg-gray-50/50 font-bold text-gray-700">
            Pacientes Sumidos (Prontos para Reativação)
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 text-gray-400 text-xs uppercase text-left">
                <tr>
                  <th className="px-6 py-4">Paciente</th>
                  <th className="px-6 py-4">Última Visita</th>
                  <th className="px-6 py-4 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {candidates.length > 0 ? candidates.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-gray-800">{p.name}</div>
                      <div className="text-xs text-gray-500">{p.phone}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {p.last_visit}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => triggerBot(p)}
                        className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-green-200"
                      >
                        <MessageSquare size={14}/> Reativar no Zap
                      </button>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={3} className="px-6 py-8 text-center text-gray-400 italic">
                      Nenhum paciente pendente de reativação no momento.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}