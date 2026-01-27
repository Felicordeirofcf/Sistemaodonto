import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight, Loader2 } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true); // Alternar entre Login e Cadastro
  const [loading, setLoading] = useState(false);
  
  // Estado do Formulário
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    user_name: '',
    clinic_name: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const endpoint = isLogin ? '/login' : '/register';
    const url = `http://127.0.0.1:5000/auth${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        if (isLogin) {
          // LOGIN SUCESSO: Salvar token e redirecionar
          localStorage.setItem('odonto_token', data.token);
          localStorage.setItem('odonto_user', JSON.stringify(data.user));
          // Força recarregamento para o App pegar o estado de login (faremos isso depois)
          window.location.href = '/'; 
        } else {
          // CADASTRO SUCESSO
          alert('Conta criada! Faça login agora.');
          setIsLogin(true);
        }
      } else {
        alert(data.error || 'Erro na operação');
      }
    } catch (error) {
      alert('Erro de conexão com o servidor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl flex overflow-hidden min-h-[600px] animate-in fade-in zoom-in-95 duration-500">
        
        {/* Lado Esquerdo - Formulário */}
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
                <div className="relative">
                  <input required name="user_name" placeholder="Seu Nome Completo" className="w-full pl-4 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all" onChange={handleChange} />
                </div>
                <div className="relative">
                  <input required name="clinic_name" placeholder="Nome da Clínica" className="w-full pl-4 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all" onChange={handleChange} />
                </div>
              </>
            )}

            <div className="relative group">
              <Mail className="absolute left-3 top-3.5 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={20} />
              <input required name="email" type="email" placeholder="Seu E-mail" className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all" onChange={handleChange} />
            </div>

            <div className="relative group">
              <Lock className="absolute left-3 top-3.5 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={20} />
              <input required name="password" type="password" placeholder="Sua Senha" className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition-all" onChange={handleChange} />
            </div>

            <button disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg mt-6 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-900/20 active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed">
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
              <button 
                onClick={() => setIsLogin(!isLogin)} 
                className="ml-2 text-blue-600 font-bold hover:underline"
              >
                {isLogin ? 'Teste Grátis' : 'Fazer Login'}
              </button>
            </p>
          </div>
        </div>

        {/* Lado Direito - Decorativo (SaaS Vibe) */}
        <div className="hidden md:flex w-1/2 bg-blue-50 relative items-center justify-center p-12 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-indigo-700 opacity-90"></div>
          <div className="relative z-10 text-white">
            <h2 className="text-4xl font-bold mb-6">Gestão Inteligente para Odontologia</h2>
            <ul className="space-y-4 text-blue-100">
              <li className="flex items-center gap-3"><div className="w-2 h-2 bg-white rounded-full"></div> Odontograma 3D Interativo</li>
              <li className="flex items-center gap-3"><div className="w-2 h-2 bg-white rounded-full"></div> Controle Financeiro Automático</li>
              <li className="flex items-center gap-3"><div className="w-2 h-2 bg-white rounded-full"></div> Confirmação via IA (WhatsApp)</li>
            </ul>
          </div>
          {/* Círculos decorativos */}
          <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
          <div className="absolute -top-24 -left-24 w-64 h-64 bg-white/10 rounded-full blur-3xl"></div>
        </div>

      </div>
    </div>
  );
}