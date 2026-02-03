import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Users, Calendar, Stethoscope, 
  DollarSign, Package, MessageSquare, 
  LogOut, ShieldCheck,
  Settings, Sparkles,
  MessageCircle, Megaphone // ✅ Importado o ícone de Megaphone
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
  const userRole = localStorage.getItem('user_role') || 'admin'; // Padrão admin para demo

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/'; 
  };

  const menuItems: MenuItem[] = [
    { title: 'Dashboard', icon: LayoutDashboard, path: '/app' },
    { title: 'Agenda', icon: Calendar, path: '/app/agenda' },
    { title: 'Pacientes', icon: Users, path: '/app/pacientes' },
    { title: 'Odontograma', icon: Stethoscope, path: '/app/odontograma' },
  ];

  const adminItems: MenuItem[] = [
    { title: 'Financeiro', icon: DollarSign, path: '/app/financeiro' },
    { title: 'Estoque', icon: Package, path: '/app/estoque' },
    { title: 'Gestão da Equipe', icon: ShieldCheck, path: '/app/gestao-equipe' },
    { title: 'AtendeChat IA', icon: MessageSquare, path: '/app/atende-chat' },

    // ✅ WhatsApp (Módulo de Chat)
    { title: 'WhatsApp', icon: MessageCircle, path: '/app/whatsapp' },

    // ✅ [NOVO] Marketing & CRM (Automação de Recall)
    { title: 'Marketing & CRM', icon: Megaphone, path: '/app/marketing' },

    { title: 'Configurações', icon: Settings, path: '/app/configuracoes' },
  ];

  const finalMenu = userRole === 'admin' ? [...menuItems, ...adminItems] : menuItems;

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-950 text-white p-6 hidden md:flex flex-col shadow-2xl z-50 font-sans border-r border-slate-800/50">
      <Link to="/app" className="flex items-center gap-3 px-2 mb-12 mt-2 hover:opacity-80 transition-opacity">
        <div className="bg-blue-600 p-2.5 rounded-2xl shadow-lg shadow-blue-500/20">
          <Sparkles size={24} className="text-white" />
        </div>
        <div className="flex flex-col">
            <h1 className="text-lg font-black tracking-tighter leading-none">OdontoSys</h1>
            <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mt-1">Intelligence</span>
        </div>
      </Link>

      <nav className="flex-1 space-y-1 overflow-y-auto pr-2 custom-scrollbar">
        {finalMenu.map((item) => {
          const isActive = location.pathname === item.path || (item.submenu && location.pathname.startsWith(item.path));
          
          return (
            <div key={item.path} className="mb-2">
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-5 py-4 rounded-[1.25rem] transition-all group ${
                  isActive 
                  ? 'bg-blue-600 text-white shadow-xl shadow-blue-500/20' 
                  : 'text-slate-500 hover:bg-slate-900 hover:text-white'
                }`}
              >
                <item.icon size={20} className={isActive ? 'text-white' : 'group-hover:text-blue-400'} />
                <span className="font-black text-[11px] uppercase tracking-widest">{item.title}</span>
              </Link>
              
              {item.submenu && location.pathname.startsWith(item.path) && (
                <div className="ml-8 mt-3 space-y-3 border-l-2 border-slate-800 pl-6 animate-in slide-in-from-top-2 duration-300">
                  {item.submenu.map((sub) => (
                    <Link 
                      key={sub.path} 
                      to={sub.path}
                      className={`block text-[10px] font-black uppercase tracking-tighter transition-colors ${
                        location.pathname === sub.path ? 'text-blue-400' : 'text-slate-600 hover:text-slate-300'
                      }`}
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

      <div className="pt-6 border-t border-slate-900 mt-6">
        <button 
          onClick={handleLogout} 
          className="flex items-center gap-3 px-5 py-4 w-full rounded-[1.25rem] text-slate-500 font-black text-[11px] uppercase tracking-widest hover:text-red-500 hover:bg-red-500/5 transition-all"
        >
          <LogOut size={20} />
          <span>Encerrar Sessão</span>
        </button>
      </div>
    </aside>
  );
}