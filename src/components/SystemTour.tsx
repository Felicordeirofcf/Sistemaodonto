import React, { useState } from 'react';
import { ChevronRight, ChevronLeft, X, PlayCircle } from 'lucide-react';

const TOUR_STEPS = [
  {
    target: 'sidebar',
    title: 'Navegação Principal',
    content: 'Aqui você acessa todas as áreas do consultório, desde a Agenda até o Financeiro.',
  },
  {
    target: 'marketing-crm',
    title: 'Captura de Pacientes',
    content: 'Nesta aba, você gerencia os leads que o robô de IA traz do seu Instagram.',
  },
  {
    target: 'odontograma-3d',
    title: 'Odontograma Digital',
    content: 'Registre tratamentos em um modelo 3D realista para encantar seus pacientes.',
  },
  {
    target: 'estoque-alertas',
    title: 'Controle de Insumos',
    content: 'O sistema avisa automaticamente quando seus materiais (como anestésicos) estão acabando.',
  }
];

export function SystemTour({ onComplete }: { onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);

  const nextStep = () => {
    if (currentStep < TOUR_STEPS.length - 1) setCurrentStep(s => s + 1);
    else onComplete();
  };

  return (
    <div className="fixed inset-0 z-[10000] bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-[2.5rem] p-10 max-w-lg w-full shadow-2xl border border-white relative animate-in zoom-in duration-300">
        <button onClick={onComplete} className="absolute top-6 right-6 text-gray-400 hover:text-gray-600">
          <X size={24} />
        </button>

        <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center mb-6">
          <PlayCircle size={32} />
        </div>

        <h2 className="text-2xl font-black text-gray-800 mb-2 tracking-tight">
          {TOUR_STEPS[currentStep].title}
        </h2>
        <p className="text-gray-500 font-medium leading-relaxed mb-10">
          {TOUR_STEPS[currentStep].content}
        </p>

        <div className="flex justify-between items-center">
          <div className="flex gap-1">
            {TOUR_STEPS.map((_, i) => (
              <div key={i} className={`h-1.5 rounded-full transition-all ${i === currentStep ? 'w-8 bg-blue-600' : 'w-2 bg-gray-200'}`} />
            ))}
          </div>

          <button 
            onClick={nextStep}
            className="bg-blue-600 text-white px-8 py-3 rounded-2xl font-black text-sm uppercase tracking-widest flex items-center gap-2 hover:bg-blue-700 transition-all shadow-xl shadow-blue-100"
          >
            {currentStep === TOUR_STEPS.length - 1 ? 'Começar Agora' : 'Próximo'} 
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}