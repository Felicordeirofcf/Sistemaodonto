import { useState } from 'react';
// MUDANÇA IMPORTANTE AQUI 👇: Adicionei 'type' antes dos tipos
import { GeometricTooth, type ToothFace, type ToothState } from '../components/GeometricTooth';
import { Save, User, Eraser, AlertCircle, CheckCircle, Activity } from 'lucide-react';

// Tipos locais
type TreatmentType = 'caries' | 'restoration' | 'canal' | 'extraction' | 'implant' | null;

interface FullMouthState {
  [toothId: number]: ToothState;
}

export function Odontograma() {
  const [mouth, setMouth] = useState<FullMouthState>({});
  const [selectedTool, setSelectedTool] = useState<TreatmentType>(null);

  const upperArcade = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lowerArcade = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  const handleToothClick = (id: number, face: ToothFace) => {
    if (selectedTool === undefined) return; 
    
    setMouth(prev => {
      const toothData = prev[id] || {};
      
      if (selectedTool === null) {
         const newData = { ...toothData };
         delete newData[face];
         return { ...prev, [id]: newData };
      }

      return {
        ...prev,
        [id]: { ...toothData, [face]: selectedTool }
      };
    });
  };

  const ToolButton = ({ type, label, color, icon: Icon }: any) => (
    <button
      onClick={() => setSelectedTool(type)}
      className={`w-full p-3 rounded-lg flex items-center gap-3 border transition-all ${
        selectedTool === type 
          ? 'bg-gray-800 text-white border-gray-800 shadow-md transform scale-105' 
          : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
      }`}
    >
      <div className={`p-1.5 rounded ${color === 'eraser' ? 'bg-gray-200' : ''}`} style={{ backgroundColor: color !== 'eraser' ? color : undefined }}>
         {Icon && <Icon size={16} className={color === 'eraser' ? 'text-gray-600' : 'text-white'} />}
      </div>
      <span className="font-medium text-sm">{label}</span>
    </button>
  );

  return (
    <div className="flex h-screen bg-gray-100">
      
      {/* LADO ESQUERDO: Mapa Visual */}
      <div className="flex-1 p-8 overflow-y-auto">
        <header className="mb-8 flex justify-between items-center">
          <div>
             <h1 className="text-2xl font-bold text-gray-800">Odontograma Avançado</h1>
             <p className="text-gray-500 flex items-center gap-2 text-sm mt-1">
               <User size={14}/> Paciente: Carlos Eduardo (Prontuário #1029)
             </p>
          </div>
          <button className="bg-primary text-white px-6 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 shadow-lg shadow-blue-200">
            <Save size={18} /> Salvar Evolução
          </button>
        </header>

        <div className="bg-white p-10 rounded-2xl shadow-sm border border-gray-200 flex flex-col items-center gap-8 min-h-[500px] justify-center">
            
            <div className={`px-4 py-2 rounded-full text-sm font-bold mb-4 ${
                selectedTool ? 'bg-blue-100 text-blue-700 animate-pulse' : 'bg-gray-100 text-gray-500'
            }`}>
                {selectedTool 
                  ? 'Modo de Pintura Ativo: Clique nas partes do dente' 
                  : 'Selecione uma ferramenta ao lado para começar'}
            </div>

            {/* Arcada Superior */}
            <div className="flex gap-1 justify-center flex-wrap max-w-4xl">
                {upperArcade.map(id => (
                    <GeometricTooth 
                        key={id} 
                        id={id} 
                        data={mouth[id] || {}} 
                        onFaceClick={(face) => handleToothClick(id, face)} 
                    />
                ))}
            </div>

            <div className="w-full max-w-4xl border-t-2 border-dashed border-gray-200 my-2"></div>

            {/* Arcada Inferior */}
            <div className="flex gap-1 justify-center flex-wrap max-w-4xl">
                {lowerArcade.map(id => (
                    <GeometricTooth 
                        key={id} 
                        id={id} 
                        data={mouth[id] || {}} 
                        onFaceClick={(face) => handleToothClick(id, face)} 
                    />
                ))}
            </div>
        </div>
      </div>

      {/* LADO DIREITO: Ferramentas */}
      <aside className="w-80 bg-white border-l border-gray-200 p-6 shadow-xl z-20">
        <h2 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
            <Activity className="text-primary"/> Ferramentas
        </h2>

        <div className="space-y-3">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Tratamentos</p>
            <ToolButton type="caries" label="Cárie / Lesão" color="#ef4444" icon={AlertCircle} />
            <ToolButton type="restoration" label="Restauração" color="#3b82f6" icon={CheckCircle} />
            <ToolButton type="canal" label="Canal (Endo)" color="#22c55e" icon={Activity} />
            <ToolButton type="implant" label="Implante" color="#a855f7" icon={Activity} />
            <ToolButton type="extraction" label="Extração (X)" color="#1f2937" icon={Activity} />

            <div className="h-4"></div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Correção</p>
            
            <button
                onClick={() => setSelectedTool(null)}
                className={`w-full p-3 rounded-lg flex items-center gap-3 border transition-all ${
                    selectedTool === null 
                    ? 'bg-gray-100 text-gray-800 border-gray-300 ring-2 ring-gray-200' 
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
            >
                <Eraser size={18} /> Borracha / Limpar
            </button>
        </div>
      </aside>
    </div>
  );
}