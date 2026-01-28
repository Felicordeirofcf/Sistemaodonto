import React, { useState } from 'react';
import { 
  Settings, Image as ImageIcon, Shield, User, Save, 
  Bot, Palette, CreditCard, Upload, Loader2, Sparkles 
} from 'lucide-react';

export function Configuracoes() {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'geral' | 'ia' | 'perfil'>('geral');
  
  // Dados simulando o que vem do seu backend/localStorage
  const user = JSON.parse(localStorage.getItem('odonto_user') || '{"clinic": "OdontoSys Premium", "plan": "gold"}');

  const [config, setConfig] = useState({
    clinic_name: user.clinic,
    plan: user.plan,
    ai_tone: 'Profissional e Acolhedor',
    ai_active: true,
    primary_color: '#2563eb'
  });

  const handleSave = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      alert('Configurações aplicadas com sucesso!');
    }, 1000);
  };

  const limits: any = {
    bronze: { label: 'Bronze', dentists: 1, color: 'text-orange-600', bg: 'bg-orange-50' },
    silver: { label: 'Prata', dentists: 5, color: 'text-slate-400', bg: 'bg-slate-50' },
    gold: { label: 'Ouro', dentists: 10, color: 'text-yellow-600', bg: 'bg-yellow-50' }
  };

  const currentLimit = limits[config.plan] || limits.bronze;

  const TabButton = ({ id, label, icon: Icon }: any) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`w-full flex items-center gap-3 px-6 py-4 rounded-2xl font-black text-[10px] uppercase tracking-widest transition-all ${
        activeTab === id 
          ? 'bg-blue-600 text-white shadow-xl shadow-blue-100' 
          : 'text-gray-400 hover:bg-white hover:text-gray-600'
      }`}
    >
      <Icon size={18} /> {label}
    </button>
  );

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <div className="max-w-5xl mx-auto">
        <header className="mb-12 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-black text-gray-900 tracking-tight flex items-center gap-3">
              <Settings className="text-blue-600" size={32} /> Central de Controle
            </h1>
            <p className="text-gray-500 font-medium mt-2">Personalize a identidade e a inteligência da sua clínica.</p>
          </div>
          
          <button 
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-3 px-10 py-4 bg-gray-900 text-white rounded-[1.5rem] font-black text-xs uppercase tracking-[0.2em] hover:bg-black transition-all shadow-xl shadow-gray-200 disabled:opacity-50 active:scale-95"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
            {loading ? 'Salvando...' : 'Salvar Alterações'}
          </button>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Menu Lateral */}
          <aside className="space-y-3">
            <TabButton id="geral" label="Geral & Plano" icon={Shield} />
            <TabButton id="ia" label="Robô de IA" icon={Bot} />
            <TabButton id="perfil" label="Minha Conta" icon={User} />
          </aside>

          {/* Área de Conteúdo */}
          <div className="md:col-span-3 space-y-8">
            
            {activeTab === 'geral' && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300 space-y-8">
                {/* Card de Plano SaaS */}
                <div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-gray-100 relative overflow-hidden">
                  <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-6">Assinatura Ativa</h3>
                  <div className={`flex items-center justify-between p-6 ${currentLimit.bg} rounded-[2rem] border border-gray-100`}>
                    <div className="flex items-center gap-5">
                      <div className="p-4 bg-white rounded-2xl shadow-sm">
                        <CreditCard className={currentLimit.color} size={28} />
                      </div>
                      <div>
                        <span className={`text-[10px] font-black uppercase tracking-widest ${currentLimit.color}`}>
                          Plano {currentLimit.label}
                        </span>
                        <p className="text-sm font-bold text-gray-600 mt-1">Capacidade: {currentLimit.dentists} dentista(s) ativo(s).</p>
                      </div>
                    </div>
                    <button className="bg-white text-blue-600 px-6 py-3 rounded-xl font-black text-[10px] uppercase tracking-widest shadow-sm hover:shadow-md transition-all">Fazer Upgrade</button>
                  </div>
                </div>

                {/* Identidade Visual */}
                <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-gray-100">
                  <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-8">Identidade da Clínica</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Nome Comercial</label>
                      <input 
                        type="text" 
                        value={config.clinic_name}
                        onChange={(e) => setConfig({...config, clinic_name: e.target.value})}
                        className="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none font-bold transition-all"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Logotipo</label>
                      <div className="flex items-center gap-5">
                        <div className="w-16 h-16 bg-blue-50 border-2 border-dashed border-blue-100 rounded-2xl flex items-center justify-center text-blue-400">
                          <Upload size={24} />
                        </div>
                        <button className="px-5 py-3 border border-gray-100 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-gray-50 transition-all">Upload PNG</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'ia' && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300 space-y-8">
                <div className="bg-white p-10 rounded-[2.5rem] shadow-sm border border-gray-100">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="p-3 bg-blue-600 rounded-2xl text-white shadow-lg shadow-blue-100">
                      <Bot size={24} />
                    </div>
                    <div>
                      <h3 className="text-xl font-black text-gray-800 tracking-tight">AtendeChat IA</h3>
                      <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Configuração do Assistente Virtual</p>
                    </div>
                  </div>

                  <div className="space-y-8">
                    <div className="flex items-center justify-between p-6 bg-blue-50/50 rounded-[2rem] border border-blue-50">
                      <div className="flex items-center gap-3">
                        <Sparkles className="text-blue-600" size={20} />
                        <span className="text-sm font-black text-blue-900 uppercase tracking-tighter">Status do Robô: ATIVO</span>
                      </div>
                      <div className="w-12 h-6 bg-blue-600 rounded-full relative cursor-pointer">
                        <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase text-gray-400 ml-2">Tom de Voz da IA</label>
                      <select 
                        className="w-full px-5 py-4 bg-gray-50 border border-gray-100 rounded-2xl outline-none font-bold"
                        value={config.ai_tone}
                        onChange={(e) => setConfig({...config, ai_tone: e.target.value})}
                      >
                        <option>Profissional e Acolhedor</option>
                        <option>Direto e Técnico</option>
                        <option>Descontraído e Amigável</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}