import { useState } from 'react';
import { GeometricTooth, type ToothFace, type ToothState } from '../components/GeometricTooth';
import { Save, User, Eraser, AlertCircle, CheckCircle, Activity } from 'lucide-react';

type TreatmentType = 'caries' | 'restoration' | 'canal' | 'extraction' | 'implant' | null;

export function Odontograma() {
  const [mouth, setMouth] = useState<{[id: number]: ToothState}>({});
  const [selectedTool, setSelectedTool] = useState<TreatmentType>(null);
  const upperArcade = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lowerArcade = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  const handleToothClick = (id: number, face: ToothFace) => {
    if (selectedTool === undefined) return; 
    setMouth(prev => {
      const toothData = prev[id] || {};
      if (selectedTool === null) {
         const newData = { ...toothData }; delete newData[face]; return { ...prev, [id]: newData };
      }
      return { ...prev, [id]: { ...toothData, [face]: selectedTool } };
    });
  };

  const ToolButton = ({ type, label, color, icon: Icon }: any) => (
    <button onClick={() => setSelectedTool(type)} className={`w-full p-2.5 rounded-lg flex items-center gap-3 border transition-all text-xs font-medium ${selectedTool === type ? 'bg-gray-800 text-white border-gray-800 shadow-md' : 'bg-white border-gray-100 text-gray-600 hover:bg-gray-50'}`}>
      <div className={`p-1 rounded ${color === 'eraser' ? 'bg-gray-200' : ''}`} style={{ backgroundColor: color !== 'eraser' ? color : undefined }}>
         {Icon && <Icon size={12} className={color === 'eraser' ? 'text-gray-600' : 'text-white'} />}
      </div>
      {label}
    </button>
  );

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-50 overflow-hidden font-sans text-sm">
      <div className="flex-1 p-4 overflow-y-auto order-2 md:order-1 flex flex-col items-center">
        <header className="w-full flex justify-between items-center mb-6 max-w-5xl">
          <div>
             <h1 className="text-xl font-bold text-gray-800">Odontograma</h1>
             <p className="text-gray-500 flex items-center gap-2 text-xs mt-0.5"><User size={12}/> Paciente: Carlos Eduardo</p>
          </div>
          <button className="bg-primary text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 shadow-sm text-xs font-bold">
            <Save size={14} /> Salvar
          </button>
        </header>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col items-center gap-6 w-full max-w-5xl flex-1 justify-center">
            <div className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wide ${selectedTool ? 'bg-blue-50 text-blue-700' : 'bg-gray-100 text-gray-500'}`}>
                {selectedTool ? 'Modo de Edição Ativo' : 'Selecione uma ferramenta'}
            </div>
            
            {/* DENTES LEVEMENTE MENORES (Scale transform no CSS se necessário, mas aqui o container limita) */}
            <div className="scale-90 md:scale-100 origin-center">
              <div className="flex gap-1 justify-center flex-wrap mb-4">
                  {upperArcade.map(id => <GeometricTooth key={id} id={id} data={mouth[id] || {}} onFaceClick={(face) => handleToothClick(id, face)} />)}
              </div>
              <div className="flex gap-1 justify-center flex-wrap">
                  {lowerArcade.map(id => <GeometricTooth key={id} id={id} data={mouth[id] || {}} onFaceClick={(face) => handleToothClick(id, face)} />)}
              </div>
            </div>
        </div>
      </div>

      <aside className="w-full md:w-72 bg-white border-l border-gray-100 p-4 shadow-xl z-20 order-1 md:order-2">
        <h2 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2"><Activity size={14} className="text-primary"/> Ferramentas</h2>
        <div className="space-y-2">
            <ToolButton type="caries" label="Cárie" color="#ef4444" icon={AlertCircle} />
            <ToolButton type="restoration" label="Restauração" color="#3b82f6" icon={CheckCircle} />
            <ToolButton type="canal" label="Canal (Endo)" color="#22c55e" icon={Activity} />
            <ToolButton type="implant" label="Implante" color="#a855f7" icon={Activity} />
            <ToolButton type="extraction" label="Extração" color="#1f2937" icon={Activity} />
            <div className="h-2"></div>
            <button onClick={() => setSelectedTool(null)} className={`w-full p-2.5 rounded-lg flex items-center gap-3 border transition-all text-xs font-medium ${selectedTool === null ? 'bg-gray-100 text-gray-800 ring-1 ring-gray-300' : 'bg-white hover:bg-gray-50'}`}>
                <Eraser size={14} /> Borracha
            </button>
        </div>
      </aside>
    </div>
  );
}