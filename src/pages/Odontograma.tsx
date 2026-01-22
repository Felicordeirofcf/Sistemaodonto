import { useState } from 'react';
import { GeometricTooth, type ToothFace, type ToothState } from '../components/GeometricTooth';
import { Save, User, Eraser, AlertCircle, CheckCircle, Activity } from 'lucide-react';

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
    // MUDANÇA: flex-col (vertical) no mobile, md:flex-row (horizontal) no PC
    <div className="flex flex-col md:flex-row h-screen bg-gray-100 overflow-hidden">
      
      {/* LADO ESQUERDO (Mapa): Ordem 2 no mobile (embaixo), Ordem 1 no PC */}
      <div className="flex-1 p-4 md:p-8 overflow-y-auto order-2 md:order-1 pb-24">
        <header className="mb-4 md:mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
             <h1 className="text-2xl font-bold text-gray-800">Odontograma Avançado</h1>
             <p className="text-gray-500 flex items-center gap-2 text-sm mt-1">
               <User size={14}/> Paciente: Carlos Eduardo
             </p>
          </div>
          <button className="w-full md:w-auto bg-primary text-white px-6 py-2 rounded-lg flex items-center justify-center gap-2 hover:bg-blue-700 shadow-lg shadow-blue-200">
            <Save size={18} /> Salvar
          </button>
        </header>

        <div className="bg-white p-4 md:p-10 rounded-2xl shadow-sm border border-gray-200 flex flex-col items-center gap-8 min-h-[400px] justify-center">
            
            <div className={`px-4 py-2 rounded-full text-xs md:text-sm font-bold mb-4 text-center ${
                selectedTool ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
            }`}>
                {selectedTool 
                  ? 'Modo Pintura Ativo' 
                  : 'Selecione uma ferramenta'}
            </div>

            {/* Arcadas com wrap para não quebrar no mobile */}
            <div className="flex gap-1 justify-center flex-wrap max-w-4xl">
                {upperArcade.map(id => (
                    <GeometricTooth 
                        key={id} id={id} data={mouth[id] || {}} 
                        onFaceClick={(face) => handleToothClick(id, face)} 
                    />
                ))}
            </div>

            <div className="w-full max-w-4xl border-t-2 border-dashed border-gray-200 my-2"></div>

            <div className="flex gap-1 justify-center flex-wrap max-w-4xl">
                {lowerArcade.map(id => (
                    <GeometricTooth 
                        key={id} id={id} data={mouth[id] || {}} 
                        onFaceClick={(face) => handleToothClick(id, face)} 
                    />
                ))}
            </div>
        </div>
      </div>

      {/* LADO DIREITO (Ferramentas): Ordem 1 no mobile (em cima), Ordem 2 no PC */}
      <aside className="w-full md:w-80 bg-white border-l border-gray-200 p-4 md:p-6 shadow-xl z-20 order-1 md:order-2 overflow-x-auto md:overflow-visible">
        <div className="flex md:flex-col gap-3 min-w-max md:min-w-0">
            {/* Cabeçalho some no mobile pra economizar espaço */}
            <h2 className="hidden md:flex text-lg font-bold text-gray-800 mb-2 items-center gap-2">
                <Activity className="text-primary"/> Ferramentas
            </h2>

            {/* Botões horizontais no mobile, verticais no PC */}
            <div className="flex md:flex-col gap-2">
              <ToolButton type="caries" label="Cárie" color="#ef4444" icon={AlertCircle} />
              <ToolButton type="restoration" label="Restauro" color="#3b82f6" icon={CheckCircle} />
              <ToolButton type="canal" label="Canal" color="#22c55e" icon={Activity} />
              <ToolButton type="implant" label="Implante" color="#a855f7" icon={Activity} />
              <ToolButton type="extraction" label="Extração" color="#1f2937" icon={Activity} />
              
              <button onClick={() => setSelectedTool(null)} className={`p-3 rounded-lg flex items-center justify-center gap-2 border ${selectedTool === null ? 'bg-gray-200' : 'bg-white'}`}>
                  <Eraser size={18} /> <span className="hidden md:inline">Borracha</span>
              </button>
            </div>
        </div>
      </aside>
    </div>
  );
}