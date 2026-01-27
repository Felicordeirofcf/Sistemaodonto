import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Users, Calendar, Stethoscope, 
  DollarSign, Package, BarChart3, MessageSquare, 
  LogOut, Target, FlaskConical, ShieldCheck 
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface SubMenuItem {
  title: string;
  path: string;
}

interface MenuItem {
  title: string;
  icon: LucideIcon;
  path: string;
  submenu?: SubMenuItem[];
}

export function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const userRole = localStorage.getItem('user_role') || 'dentist';

  const handleLogout = () => {
    localStorage.removeItem('odonto_token');
    localStorage.removeItem('user_role');
    navigate('/login');
  };

  // Ajustamos os caminhos para incluir o prefixo /app
  const menuItems: MenuItem[] = [
    { title: 'Dashboard', icon: LayoutDashboard, path: '/app' },
    { title: 'Agenda', icon: Calendar, path: '/app/agenda' },
    { title: 'Pacientes', icon: Users, path: '/app/pacientes' },
    { title: 'Odontograma', icon: Stethoscope, path: '/app/odontograma' },
  ];

  const adminItems: MenuItem[] = [
    { 
      title: 'Marketing & CRM', 
      icon: Target, 
      path: '/app/marketing',
      submenu: [
        { title: 'Funil de Leads', path: '/app/marketing' },
        { title: 'Campanhas Bot', path: '/app/marketing/campanhas' }
      ]
    },
    { title: 'Financeiro', icon: DollarSign, path: '/app/financeiro' },
    { title: 'Dashboard Vendas', icon: BarChart3, path: '/app/dashboard-vendas' },
    { title: 'Estoque', icon: Package, path: '/app/estoque' },
    { title: 'Fichas Técnicas', icon: FlaskConical, path: '/app/config-procedimentos' },
    { title: 'Gestão da Equipe', icon: ShieldCheck, path: '/app/gestao-equipe' },
    { title: 'AtendeChat IA', icon: MessageSquare, path: '/app/atende-chat' },
  ];

  const finalMenu = userRole === 'admin' ? [...menuItems, ...adminItems] : menuItems;

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-900 text-white p-4 hidden md:flex flex-col shadow-xl z-50">
      <div className="flex items-center gap-3 px-2 mb-10 mt-4">
        <div className="bg-blue-600 p-2 rounded-lg">
          <Stethoscope size={24} className="text-white" />
        </div>
        <h1 className="text-xl font-bold tracking-tight">OdontoSys</h1>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto pr-2 custom-scrollbar">
        {finalMenu.map((item) => {
          const isActive = location.pathname === item.path || (item.submenu && location.pathname.startsWith(item.path));
          
          return (
            <div key={item.path} className="mb-1">
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <item.icon size={20} />
                <span className="font-medium">{item.title}</span>
              </Link>
              
              {item.submenu && location.pathname.startsWith(item.path) && (
                <div className="ml-12 mt-2 space-y-2 border-l border-slate-700 pl-4">
                  {item.submenu.map((sub) => (
                    <Link 
                      key={sub.path} 
                      to={sub.path}
                      className={`block py-1 text-sm ${location.pathname === sub.path ? 'text-blue-400 font-bold' : 'text-slate-500'}`}
                    >
                      {sub.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      <div className="pt-4 border-t border-slate-800 mt-4">
        <button onClick={handleLogout} className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-slate-400 hover:text-red-500 transition-all">
          <LogOut size={20} />
          <span className="font-medium">Sair</span>
        </button>
      </div>
    </aside>
  );
}