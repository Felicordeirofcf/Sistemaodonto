import React, { useState, useEffect } from 'react';
import { Settings, Image as ImageIcon, Shield, User, Save, CheckCircle } from 'lucide-react';

export function Configuracoes() {
  const [loading, setLoading] = useState(false);
  const user = JSON.parse(localStorage.getItem('odonto_user') || '{}');
  const role = localStorage.getItem('user_role');

  const [config, setConfig] = useState({
    clinic_name: user.clinic || 'Minha Clínica',
    plan: user.plan || 'bronze',
    email_notificacoes: true
  });

  const handleSave = () => {
    setLoading(true);
    // Simulação de salvamento local e feedback visual
    setTimeout(() => {
      setLoading(false);
      alert('Configurações atualizadas com sucesso!');
    }, 1000);
  };

  const limits: any = {
    bronze: { label: 'Bronze', dentists: 1, color: 'text-orange-600' },
    silver: { label: 'Prata', dentists: 5, color: 'text-slate-400' },
    gold: { label: 'Ouro', dentists: 10, color: 'text-yellow-600' }
  };

  const currentLimit = limits[config.plan] || limits.bronze;

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Settings className="text-blue-600" /> Configurações da Clínica
          </h1>
          <p className="text-gray-500 text-sm">Gerencie a identidade e permissões do seu sistema.</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Menu Lateral de Configurações */}
          <div className="space-y-2">
            <button className="w-full flex items-center gap-3 px-4 py-3 bg-blue-600 text-white rounded-xl font-bold shadow-lg shadow-blue-200 transition-all">
              <Shield size={18} /> Geral & Plano
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-white rounded-xl transition-all">
              <ImageIcon size={18} /> Logotipo e Cores
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-white rounded-xl transition-all">
              <User size={18} /> Minha Conta
            </button>
          </div>

          {/* Área de Conteúdo */}
          <div className="md:col-span-2 space-y-6">
            {/* Card de Plano */}
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-gray-800 mb-4">Seu Plano Atual</h3>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-2xl border border-gray-100">
                <div>
                  <span className={`text-xs font-black uppercase tracking-widest ${currentLimit.color}`}>
                    Plano {currentLimit.label}
                  </span>
                  <p className="text-sm text-gray-500">Capacidade para até {currentLimit.dentists} dentista(s).</p>
                </div>
                <button className="text-blue-600 text-sm font-bold hover:underline">Fazer Upgrade</button>
              </div>
            </div>

            {/* Formulário de Identidade */}
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-gray-800 mb-6">Informações da Clínica</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase mb-1 block ml-1">Nome de Exibição</label>
                  <input 
                    type="text" 
                    value={config.clinic_name}
                    onChange={(e) => setConfig({...config, clinic_name: e.target.value})}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>
                
                {/* Upload de Logo (Simulação Visual) */}
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase mb-1 block ml-1">Logotipo da Clínica</label>
                  <div className="mt-2 flex items-center gap-4">
                    <div className="w-20 h-20 bg-blue-50 border-2 border-dashed border-blue-200 rounded-2xl flex items-center justify-center text-blue-400">
                      <ImageIcon size={32} />
                    </div>
                    <button className="px-4 py-2 border border-gray-200 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all">
                      Alterar Foto
                    </button>
                  </div>
                </div>
              </div>

              <div className="mt-10 pt-6 border-t border-gray-100 flex justify-end">
                <button 
                  onClick={handleSave}
                  disabled={loading}
                  className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 transition-all shadow-xl shadow-blue-200 disabled:opacity-50"
                >
                  {loading ? 'Salvando...' : <><Save size={18} /> Salvar Alterações</>}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}