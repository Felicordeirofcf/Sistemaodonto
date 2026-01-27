import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Zap, TrendingUp, CheckCircle } from 'lucide-react';

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="bg-white text-slate-900 font-sans">
      {/* Hero Section */}
      <section className="pt-20 pb-32 bg-gradient-to-b from-blue-50 to-white px-6 text-center">
        <h1 className="text-5xl md:text-6xl font-extrabold mb-6 tracking-tight">
          Sua clínica com <span className="text-blue-600">cadeira cheia</span> todos os dias.
        </h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-10">
          O OdontoSys usa Inteligência Artificial para identificar pacientes sumidos e automatizar sua agenda.
        </p>
        <div className="flex justify-center gap-4">
          {/* Agora envia o modo register para o Login.tsx abrir no cadastro */}
          <button 
            onClick={() => navigate('/login?mode=register')} 
            className="px-8 py-4 bg-blue-600 text-white rounded-2xl font-bold shadow-xl hover:bg-blue-700 transition-all active:scale-95"
          >
            Começar Teste Grátis
          </button>
        </div>
      </section>

      {/* Diferenciais */}
      <section className="py-20 px-6 max-w-6xl mx-auto grid md:grid-cols-3 gap-12">
        <div className="text-center">
          <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Zap size={32} />
          </div>
          <h3 className="text-xl font-bold mb-3">Robô de Reativação</h3>
          <p className="text-slate-500">Nossa IA identifica pacientes que não voltam há 6 meses e sugere o agendamento automático.</p>
        </div>
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 text-green-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <TrendingUp size={32} />
          </div>
          <h3 className="text-xl font-bold mb-3">Lucro Real</h3>
          <p className="text-slate-500">Cálculo automático de ROI. Saiba exatamente quanto sobrou após descontar o custo do material.</p>
        </div>
        <div className="text-center">
          <div className="w-16 h-16 bg-purple-100 text-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Shield size={32} />
          </div>
          <h3 className="text-xl font-bold mb-3">Segurança SaaS</h3>
          <p className="text-slate-500">Dados criptografados e isolados por clínica. Acesse de qualquer lugar, a qualquer hora.</p>
        </div>
      </section>

      {/* Planos */}
      <section className="py-20 bg-slate-50 px-6">
        <h2 className="text-3xl font-bold text-center mb-16">Escolha o plano ideal para sua clínica</h2>
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8">
          {[
            { name: 'Bronze', price: '197', limit: '1 Dentista' },
            { name: 'Prata', price: '397', limit: '5 Dentistas' },
            { name: 'Ouro', price: '697', limit: '10 Dentistas' },
          ].map((plan) => (
            <div key={plan.name} className="bg-white p-8 rounded-3xl shadow-sm border border-slate-200 text-center hover:border-blue-500 transition-all">
              <h4 className="text-lg font-bold text-slate-500 mb-2">{plan.name}</h4>
              <div className="text-4xl font-black mb-6">R$ {plan.price}<span className="text-sm text-slate-400">/mês</span></div>
              <ul className="text-left space-y-4 mb-8">
                <li className="flex items-center gap-2 text-sm"><CheckCircle size={16} className="text-green-500" /> {plan.limit}</li>
                <li className="flex items-center gap-2 text-sm"><CheckCircle size={16} className="text-green-500" /> IA de Reativação</li>
                <li className="flex items-center gap-2 text-sm"><CheckCircle size={16} className="text-green-500" /> Dashboards Completos</li>
              </ul>
              <button 
                onClick={() => navigate('/login?mode=register')} 
                className="w-full py-3 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 transition-all active:scale-95"
              >
                Assinar Agora
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}