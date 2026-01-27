import { useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Calendar, 
  DollarSign, 
  MessageSquare, 
  Box, 
  Activity, 
  Sparkles,
  LogOut 
} from 'lucide-react';
import { useEffect, useState } from 'react';

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Estado para armazenar dados do usuário logado
  const [user, setUser] = useState({ name: 'Usuário', clinic: 'Minha Clínica' });

  useEffect(() => {
    // Carrega dados do localStorage
    const storedUser = localStorage.getItem('odonto_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error("Erro ao carregar usuário na sidebar");
      }
    }
  }, []);

  const handleLogout = () => {
    // Limpa os dados de sessão
    localStorage.removeItem('odonto_token');
    localStorage.removeItem('odonto_user');
    // Redireciona para login
    window.location.href = '/login';
  };

  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Activity, label: 'Odontograma', path: '/odontograma' },
    { icon: Sparkles, label: 'Harmonização', path: '/harmonizacao' },
    { icon: Calendar, label: 'Agenda', path: '/agenda' },
    { icon: Users, label: 'Pacientes', path: '/pacientes' },
    { icon: DollarSign, label: 'Financeiro', path: '/financeiro' },
    { icon: MessageSquare, label: 'Marketing', path: '/marketing' },
    { icon: Box, label: 'Estoque', path: '/estoque' },
    { icon: MessageSquare, label: 'AtendeChat AI', path: '/atende-chat' },
  ];

  return (
    <aside className="w-64 bg-[#0F172A] text-gray-300 h-screen fixed left-0 top-0 flex flex-col transition-all duration-300 z-50 hidden md:flex">
      {/* Logo */}
      <div className="p-6 flex items-center gap-3 text-white mb-2">
        <div className="w-8 h-8 bg-gradient-to-tr from-green-400 to-blue-500 rounded-lg flex items-center justify-center shadow-lg shadow-green-500/20">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="w-5 h-5 text-white">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        <span className="text-xl font-bold tracking-tight">OdontoSys</span>
      </div>

      {/* Menu */}
      <nav className="flex-1 px-4 space-y-1 overflow-y-auto custom-scrollbar">
        <div className="text-xs font-bold text-gray-500 uppercase px-4 mb-2 mt-4 tracking-wider">Menu Principal</div>
        
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50 scale-[1.02]' 
                  : 'hover:bg-white/5 hover:text-white'
              }`}
            >
              <item.icon size={20} className={`transition-colors ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'}`} />
              <span className="font-medium text-sm">{item.label}</span>
              {isActive && <div className="ml-auto w-1.5 h-1.5 bg-white rounded-full"></div>}
            </button>
          );
        })}
      </nav>

      {/* Perfil do Usuário no Rodapé */}
      <div className="p-4 bg-[#0B1120]">
        <div className="flex items-center gap-3 p-3 bg-white/5 rounded-2xl border border-white/5 hover:border-white/10 transition-colors">
          <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center font-bold text-white shadow-lg shrink-0">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-white truncate">{user.name}</p>
            <p className="text-[10px] text-gray-400 truncate">{user.clinic}</p>
          </div>
          <button 
            onClick={handleLogout} 
            title="Sair do sistema" 
            className="p-2 text-gray-400 hover:text-red-400 hover:bg-white/5 rounded-lg transition-colors"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
}