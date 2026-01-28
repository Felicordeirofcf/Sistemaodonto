import React, { useState, useEffect } from 'react';
import { 
  Megaphone, 
  Target, 
  Users, 
  TrendingUp, 
  DollarSign, 
  Facebook, 
  CheckCircle,
  AlertCircle,
  Zap,
  MessageSquare
} from 'lucide-react';

// Tipagem para o SDK do Facebook (evita erro de TS)
declare global {
  interface Window {
    fbAsyncInit: () => void;
    FB: any;
  }
}

const MarketingCRM = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [budget, setBudget] = useState(300);
  const [stats, setStats] = useState({
    spend: 0.0,
    clicks: 0,
    cpc: 0.0,
    leads: 0
  });
  const [loading, setLoading] = useState(false);

  // 1. INICIALIZA O SDK DO FACEBOOK AO CARREGAR A PÁGINA
  useEffect(() => {
    window.fbAsyncInit = function() {
      window.FB.init({
        appId      : '928590639502117', // <--- COLOQUE O NÚMERO DO ID AQUI!
        cookie     : true,
        xfbml      : true,
        version    : 'v19.0'
      });
    };

    // Carrega o script do Facebook de forma assíncrona
    (function(d, s, id){
       var js, fjs = d.getElementsByTagName(s)[0];
       if (d.getElementById(id)) {return;}
       js = d.createElement(s); js.id = id;
       // @ts-ignore
       js.src = "https://connect.facebook.net/pt_BR/sdk.js";
       // @ts-ignore
       fjs.parentNode.insertBefore(js, fjs);
     }(document, 'script', 'facebook-jssdk'));

     // Verifica se já temos dados salvos no banco
     checkConnectionStatus();
  }, []);

  const checkConnectionStatus = async () => {
    // Tenta sincronizar para ver se o token do banco ainda vale
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/marketing/meta/sync', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setIsConnected(true);
        setStats({
            spend: data.spend || 0,
            clicks: data.clicks || 0,
            cpc: data.cpc || 0,
            leads: Math.floor((data.clicks || 0) * 0.15) // Estimativa baseada em cliques
        });
      }
    } catch (error) {
      console.log("Ainda não conectado ao Meta");
    }
  };

  // 2. FUNÇÃO DE LOGIN (CHAMADA PELO BOTÃO AZUL)
  const handleFacebookLogin = () => {
    setLoading(true);
    if (!window.FB) {
        alert("Erro: Bloqueador de popups impediu o Facebook SDK.");
        setLoading(false);
        return;
    }

    window.FB.login((response: any) => {
      if (response.authResponse) {
        console.log('Bem-vindo! Buscando informações...');
        const accessToken = response.authResponse.accessToken;
        
        // 3. ENVIA O TOKEN PARA O SEU BACKEND
        sendTokenToBackend(accessToken);
      } else {
        console.log('Usuário cancelou o login ou não autorizou totalmente.');
        setLoading(false);
      }
    }, { scope: 'ads_management,ads_read' }); // Permissões necessárias
  };

  const sendTokenToBackend = async (token: string) => {
    try {
      const jwt = localStorage.getItem('token');
      // Envia para a rota REAL que criamos
      const res = await fetch('/api/marketing/meta/connect', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${jwt}`
        },
        body: JSON.stringify({ 
            accessToken: token,
            adAccountId: null // O backend vai tentar descobrir ou usar o padrão
        })
      });

      if (res.ok) {
        setIsConnected(true);
        alert("✅ Facebook conectado com sucesso! O sistema começará a otimizar seus anúncios.");
        checkConnectionStatus(); // Atualiza os números
      } else {
        const err = await res.json();
        alert("Erro ao salvar conexão: " + JSON.stringify(err));
      }
    } catch (error) {
      alert("Erro de conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-screen">
      
      {/* HEADER */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10">
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
            <Target className="h-8 w-8" />
            Automação de Vendas IA
          </h1>
          <p className="text-blue-100 max-w-xl text-lg">
            Sincronize sua conta de anúncios e deixe nossa IA captar pacientes automaticamente.
          </p>
        </div>
        <Megaphone className="absolute right-0 bottom-0 h-64 w-64 text-white opacity-10 transform translate-x-10 translate-y-10 rotate-12" />
      </div>

      {/* PAINEL PRINCIPAL */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* COLUNA 1: CONFIGURAÇÃO */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Configuração OdontoAds
            </h2>

            {!isConnected ? (
              <div className="flex flex-col items-center justify-center p-8 bg-slate-50 rounded-xl border-2 border-dashed border-slate-300">
                <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                  <Facebook className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-700 mb-2">Conecte sua conta Meta</h3>
                <p className="text-slate-500 text-center mb-6 max-w-md">
                  Para iniciar a captação automática, precisamos de permissão para ler seus anúncios e otimizar o orçamento.
                </p>
                <button 
                  onClick={handleFacebookLogin}
                  disabled={loading}
                  className="bg-[#1877F2] hover:bg-[#166fe5] text-white px-8 py-3 rounded-lg font-semibold flex items-center gap-3 transition-colors shadow-md disabled:opacity-70"
                >
                  {loading ? 'Conectando...' : 'Vincular com Facebook'}
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                  <div>
                    <p className="font-semibold text-green-800">Conta Sincronizada</p>
                    <p className="text-sm text-green-600">O robô está lendo suas métricas em tempo real.</p>
                  </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Orçamento Mensal (R$)</label>
                    <input 
                        type="range" 
                        min="300" 
                        max="5000" 
                        step="100"
                        value={budget}
                        onChange={(e) => setBudget(Number(e.target.value))}
                        className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between mt-2 text-slate-600 font-medium">
                        <span>R$ {budget},00</span>
                        <span>~{Math.floor(budget / 15)} Leads/mês</span>
                    </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* COLUNA 2: MÉTRICAS REAIS */}
        <div className="space-y-6">
             <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 className="font-bold text-slate-700 mb-4">Performance Tempo Real</h3>
                <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-100 rounded-lg"><Users className="h-5 w-5 text-blue-600"/></div>
                            <div>
                                <p className="text-sm text-slate-500">Cliques (Tráfego)</p>
                                <p className="font-bold text-slate-800">{stats.clicks}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-100 rounded-lg"><DollarSign className="h-5 w-5 text-green-600"/></div>
                            <div>
                                <p className="text-sm text-slate-500">Investido (Total)</p>
                                <p className="font-bold text-slate-800">R$ {stats.spend.toFixed(2)}</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-100 rounded-lg"><TrendingUp className="h-5 w-5 text-purple-600"/></div>
                            <div>
                                <p className="text-sm text-slate-500">Custo p/ Clique</p>
                                <p className="font-bold text-slate-800">R$ {stats.cpc.toFixed(2)}</p>
                            </div>
                        </div>
                    </div>
                </div>
             </div>
        </div>

      </div>
    </div>
  );
};

export default MarketingCRM;