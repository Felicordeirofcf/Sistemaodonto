import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Calendar, 
  Stethoscope, 
  DollarSign, 
  Package, 
  BarChart3, 
  MessageSquare, 
  Settings, 
  LogOut,
  Target,
  FlaskConical
} from 'lucide-react';

export function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('odonto_token');
    navigate('/login');
  };

  const menuItems = [
    { title: 'Dashboard', icon: LayoutDashboard, path: '/' },
    { title: 'Agenda', icon: Calendar, path: '/agenda' },
    { title: 'Pacientes', icon: Users, path: '/pacientes' },
    { title: 'Odontograma', icon: Stethoscope, path: '/odontograma' },
    { 
      title: 'Marketing & CRM', 
      icon: Target, 
      path: '/marketing',
      submenu: [
        { title: 'Funil de Leads', path: '/marketing' },
        { title: 'Campanhas Bot', path: '/marketing/campanhas' }
      ]
    },
    { title: 'Financeiro', icon: DollarSign, path: '/financeiro' },
    { title: 'Dashboard Vendas', icon: BarChart3, path: '/dashboard-vendas' },
    { title: 'Estoque', icon: Package, path: '/estoque' },
    { title: 'Fichas Técnicas', icon: FlaskConical, path: '/config-procedimentos' },
    { title: 'AtendeChat IA', icon: MessageSquare, path: '/atende-chat' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-900 text-white p-4 hidden md:flex flex-col shadow-xl z-50">
      <div className="flex items-center gap-3 px-2 mb-10 mt-4">
        <div className="bg-blue-600 p-2 rounded-lg">
          <Stethoscope size={24} className="text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight">Sistema Odonto</h1>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto pr-2 custom-scrollbar">
        {menuItems.map((item) => (
          <div key={item.path}>
            <Link
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                location.pathname === item.path 
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <item.icon size={20} className={location.pathname === item.path ? 'text-white' : 'group-hover:text-blue-400'} />
              <span className="font-medium">{item.title}</span>
            </Link>
            
            {/* Submenu para Marketing se o caminho for o atual */}
            {item.submenu && location.pathname.includes('/marketing') && (
              <div className="ml-12 mt-1 space-y-1">
                {item.submenu.map(sub => (
                  <Link 
                    key={sub.path} 
                    to={sub.path}
                    className={`block py-2 text-sm ${location.pathname === sub.path ? 'text-blue-400 font-bold' : 'text-slate-500 hover:text-slate-300'}`}
                  >
                    {sub.title}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      <div className="pt-4 border-t border-slate-800 mt-4">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-slate-400 hover:bg-red-500/10 hover:text-red-500 transition-all duration-200"
        >
          <LogOut size={20} />
          <span className="font-medium">Sair do Sistema</span>
        </button>
      </div>
    </aside>
  );
}