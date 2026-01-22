import { LayoutDashboard, Users, Banknote, Megaphone, Package, Calendar, MessageSquare } from 'lucide-react'; //
import { Link, useLocation } from 'react-router-dom';

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: Calendar, label: 'Agenda', path: '/agenda' },
  { icon: Users, label: 'Pacientes', path: '/pacientes' },
  { icon: Banknote, label: 'Financeiro', path: '/financeiro' },
  { icon: Megaphone, label: 'Marketing', path: '/marketing' },
  { icon: Package, label: 'Estoque', path: '/estoque' },
  { icon: MessageSquare, label: 'AtendeChat AI', path: '/atende-chat' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-primary text-white h-screen fixed left-0 top-0 flex flex-col shadow-xl z-50">
      <div className="p-6 text-2xl font-bold border-b border-gray-700/50 flex items-center gap-2">
        <div className="w-8 h-8 bg-accent rounded-lg"></div>
        OdontoSys
      </div>
      <nav className="flex-1 mt-6 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.label}
              to={item.path}
              className={`flex items-center gap-3 px-6 py-4 transition-all duration-200 border-l-4 ${
                isActive 
                  ? 'bg-secondary border-accent text-white' 
                  : 'border-transparent hover:bg-white/5 text-gray-400 hover:text-white'
              }`}
            >
              <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`font-medium ${isActive ? 'font-bold' : ''}`}>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      
      <div className="p-6 border-t border-gray-700/50 bg-primary/50">
        <div className="flex items-center gap-3">
          <img 
            src="https://ui-avatars.com/api/?name=Dr+Fonseca&background=0D8ABC&color=fff" 
            alt="User" 
            className="w-10 h-10 rounded-full border-2 border-accent"
          />
          <div>
            <p className="text-sm font-bold text-white">Dr. Fonseca</p>
            <p className="text-xs text-gray-400">Administrador</p>
          </div>
        </div>
      </div>
    </aside>
  );
}