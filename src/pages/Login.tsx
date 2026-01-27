import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Lock, Mail, ArrowRight, Loader2 } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const location = useLocation(); // Hook para ler parâmetros da URL
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  
  // Detecta se o usuário veio pelo botão "Teste Grátis" da Landing Page
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('mode') === 'register') {
      setIsLogin(false);
    }
  }, [location]);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    user_name: '',
    clinic_name: '',
    plan_type: 'bronze'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const endpoint = isLogin ? '/login' : '/register';
    const url = `/auth${endpoint}`; 

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        if (isLogin) {
          localStorage.setItem('odonto_token', data.token);
          localStorage.setItem('user_role', data.role); 
          localStorage.setItem('odonto_user', JSON.stringify(data.user));
          
          // Redireciona para a área interna do app
          window.location.href = '/app'; 
        } else {
          alert('Conta criada com sucesso! Faça login agora.');
          setIsLogin(true);
        }
      } else {
        alert(data.error || 'Erro na operação');
      }
    } catch (error) {
      console.error(error);
      alert('Erro de conexão com o servidor.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl flex overflow-hidden min-h-[600px]">
        
        <div className="w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center">
          <div className="mb-8">
            <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">OdontoSys</h1>
            <p className="text-gray-500 text-sm mt-2">
              {isLogin ? 'Bem-vindo de volta, doutor.' : 'Comece a gerenciar sua clínica hoje.'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <input required name="user_name" placeholder="Seu Nome Completo" className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" onChange={handleChange} />
                <input required name="clinic_name" placeholder="Nome da Clínica" className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" onChange={handleChange} />
                
                <select 
                  name="plan_type" 
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white text-gray-600"
                  onChange={(e: any) => setFormData({...formData, plan_type: e.target.value})}
                >
                  <option value="bronze">Plano Bronze (1 Dentista)</option>
                  <option value="silver">Plano Prata (5 Dentistas)</option>
                  <option value="gold">Plano Ouro (10 Dentistas)</option>
                </select>
              </>
            )}

            <div className="relative group">
              <Mail className="absolute left-3 top-3.5 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={20} />
              <input required name="email" type="email" placeholder="Seu E-mail" className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" onChange={handleChange} />
            </div>

            <div className="relative group">
              <Lock className="absolute left-3 top-3.5 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={20} />
              <input required name="password" type="password" placeholder="Sua Senha" className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" onChange={handleChange} />
            </div>

            <button disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg mt-6 transition-all flex items-center justify-center gap-2 disabled:opacity-70 shadow-lg shadow-blue-900/20">
              {loading ? <Loader2 className="animate-spin" /> : (
                <>
                  {isLogin ? 'Entrar no Sistema' : 'Criar Minha Conta'} <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              {isLogin ? 'Ainda não tem conta?' : 'Já possui cadastro?'}
              <button onClick={() => setIsLogin(!isLogin)} className="ml-2 text-blue-600 font-bold hover:underline">
                {isLogin ? 'Teste Grátis' : 'Fazer Login'}
              </button>
            </p>
          </div>
        </div>

        <div className="hidden md:flex w-1/2 bg-blue-600 relative items-center justify-center p-12 overflow-hidden">
          <div className="relative z-10 text-white">
            <h2 className="text-4xl font-bold mb-6">Gestão com IA para Odontologia</h2>
            <ul className="space-y-4 text-blue-100">
              <li className="flex items-center gap-3">✓ Odontograma Interativo</li>
              <li className="flex items-center gap-3">✓ Financeiro com Lucro Real</li>
              <li className="flex items-center gap-3">✓ Reativação de Pacientes via IA</li>
            </ul>
          </div>
          <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
        </div>
      </div>
    </div>
  );
}