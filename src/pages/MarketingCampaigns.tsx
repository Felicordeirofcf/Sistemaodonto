import { useState, useEffect } from 'react';
import { Send, Users, MessageSquare, Calendar as CalendarIcon, Zap } from 'lucide-react';

export function MarketingCampaigns() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/marketing/campaign/recall', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
    .then(res => res.json())
    .then(data => setCandidates(data))
    .catch(console.error);
  }, []);

  const triggerBot = (patient: any) => {
    // Aqui linkamos com a Agenda do médico:
    const msg = `Olá ${patient.name}! O Dr. notou que faz tempo que não nos vemos. Temos horários livres na agenda para sua revisão. Vamos marcar?`;
    const whatsappUrl = `https://wa.me/${patient.phone}?text=${encodeURIComponent(msg)}`;
    window.open(whatsappUrl, '_blank');
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Automação de Vendas</h1>
        <p className="text-gray-500">O robô identifica pacientes sumidos e sugere horários na agenda.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* CARD DE STATUS DO ROBÔ */}
        <div className="lg:col-span-1 bg-white p-6 rounded-2xl shadow-sm border border-blue-100">
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
              <span className="text-gray-500">Vagas na Agenda (Hoje):</span>
              <span className="font-bold text-green-600">4 Livres</span>
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
          <table className="w-full">
            <thead className="bg-gray-50 text-gray-400 text-xs uppercase">
              <tr>
                <th className="px-6 py-4 text-left">Paciente</th>
                <th className="px-6 py-4 text-left">Última Visita</th>
                <th className="px-6 py-4 text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {candidates.map((p: any) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-800">{p.name}</div>
                    <div className="text-xs text-gray-500">{p.phone}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(p.last_visit).toLocaleDateString()}
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
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}