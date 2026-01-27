import { useState, useEffect } from 'react';
import { Users, DollarSign, Calendar, Activity, TrendingUp, AlertTriangle } from 'lucide-react';

export function Dashboard() {
  // Inicializa com valores zerados para não quebrar o .toLocaleString()
  const [stats, setStats] = useState({
    patients: 0,
    revenue: 0,
    appointments: 0,
    low_stock: 0
  });

  const [userName, setUserName] = useState('Doutor');

  useEffect(() => {
    // 1. Pega nome do usuário
    const storedUser = localStorage.getItem('odonto_user');
    const token = localStorage.getItem('odonto_token');

    if (storedUser) {
      try {
        setUserName(JSON.parse(storedUser).name.split(' ')[0]);
      } catch (e) {}
    }

    // 2. Se não tem token, tchau!
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // 3. Busca estatísticas com tratamento de erro robusto
    fetch('http://127.0.0.1:5000/api/dashboard/stats', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
      .then(res => {
          // SE O TOKEN FOR INVÁLIDO (401 ou 422), LIMPA E MANDA PRO LOGIN
          if (res.status === 401 || res.status === 422) {
              console.warn("Token inválido ou expirado. Fazendo logout...");
              localStorage.removeItem('odonto_token');
              localStorage.removeItem('odonto_user');
              window.location.href = '/login';
              return null; // Interrompe aqui
          }
          return res.json();
      })
      .then(data => {
          // Só atualiza se vierem dados válidos
          if (data) setStats(data);
      })
      .catch(err => console.error("Erro de conexão:", err));
  }, []);

  // Função segura para formatar dinheiro
  const formatMoney = (value: number | undefined) => {
    return (value || 0).toLocaleString('pt-BR');
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Visão Geral</h1>
        <p className="text-gray-500">Bem-vindo de volta, Dr(a). {userName}.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        
        {/* Card Pacientes */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 bg-blue-50 rounded-xl text-blue-600">
              <Users size={24} />
            </div>
            <span className="flex items-center text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full">
              <TrendingUp size={12} className="mr-1"/> +2
            </span>
          </div>
          <h3 className="text-4xl font-bold text-gray-800 mb-1">{stats.patients || 0}</h3>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Pacientes Totais</p>
        </div>

        {/* Card Financeiro (AQUI ESTAVA O ERRO) */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 bg-green-50 rounded-xl text-green-600">
              <DollarSign size={24} />
            </div>
            <span className="flex items-center text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full">
              <TrendingUp size={12} className="mr-1"/> +15%
            </span>
          </div>
          <h3 className="text-4xl font-bold text-gray-800 mb-1">
            R$ {formatMoney(stats.revenue)}
          </h3>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Faturamento Dia</p>
        </div>

        {/* Card Estoque */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 bg-orange-50 rounded-xl text-orange-600">
              <AlertTriangle size={24} />
            </div>
            {stats.low_stock > 0 && (
                <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded-full animate-pulse">
                    Atenção
                </span>
            )}
          </div>
          <h3 className="text-4xl font-bold text-gray-800 mb-1">{stats.low_stock || 0}</h3>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Itens Baixo Estoque</p>
        </div>

        {/* Card Tratamentos */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="p-3 bg-purple-50 rounded-xl text-purple-600">
              <Activity size={24} />
            </div>
          </div>
          <h3 className="text-4xl font-bold text-gray-800 mb-1">8</h3>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Tratamentos Hoje</p>
        </div>
      </div>
    </div>
  );
}