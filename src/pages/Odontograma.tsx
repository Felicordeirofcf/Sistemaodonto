// @ts-nocheck
import { useState, useEffect } from 'react';
import { GeometricTooth } from '../components/GeometricTooth'; 
import { Save, User, Eraser, AlertCircle, CheckCircle, Activity, Info, Box, Layout, Skull } from 'lucide-react';
import { Skull3D } from '../components/Skull3D';

// --- TIPOS ---
export type ToothFace = 'vestibular' | 'lingual' | 'distal' | 'mesial' | 'oclusal' | 'occlusal';
export type TreatmentType = 'caries' | 'restoration' | 'canal' | 'extraction' | 'implant' | null;

export interface ToothState {
  [key: string]: TreatmentType;
}

interface ToolButtonProps {
  type: TreatmentType;
  label: string;
  color: string;
  icon: any;
}
// -------------

export function Odontograma() {
  const [mouth, setMouth] = useState<Record<number, ToothState>>({});
  const [selectedTool, setSelectedTool] = useState<TreatmentType>(null);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  
  // Estado para o Paciente Atual
  const [pacienteInfo, setPacienteInfo] = useState({ id: 1, nome: 'Carregando...' });
  const [loading, setLoading] = useState(false);

  const upperArcade = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lowerArcade = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  // 1. CARREGAR DADOS DO PACIENTE AO ABRIR (ID 1 fixo para teste)
  useEffect(() => {
    const pacienteId = 1; 
    
    // Caminho relativo para funcionar no Render
    fetch(`/api/patients/${pacienteId}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
            console.log("Crie um paciente primeiro na aba Pacientes!");
            return;
        }
        setPacienteInfo({ id: data.id, nome: data.nome });
        if (data.odontogram_data) {
            setMouth(data.odontogram_data); 
        }
      })
      .catch(err => console.error("Erro ao carregar paciente:", err));
  }, []);

  // 2. SALVAR NO BANCO
  const handleSalvarBanco = async () => {
    setLoading(true);
    try {
        const response = await fetch(`/api/patients/${pacienteInfo.id}/odontogram`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(mouth)
        });
        
        if (response.ok) {
            alert("Prontuário salvo com sucesso no banco de dados!");
        } else {
            alert("Erro ao salvar.");
        }
    } catch (error) {
        console.error(error);
        alert("Erro de conexão.");
    } finally {
        setLoading(false);
    }
  };

  const handleToothClick = (id: number, face: any) => { 
    if (selectedTool === undefined) return;

    setMouth(prev => {
      const toothData = prev[id] || {};
      
      if (selectedTool === null) {
        const newData = { ...toothData };
        delete newData[face as string];
        return { ...prev, [id]: newData };
      }
      
      if (selectedTool === 'extraction') {
        return { 
          ...prev, 
          [id]: { vestibular: 'extraction', lingual: 'extraction', mesial: 'extraction', distal: 'extraction', occlusal: 'extraction' } 
        };
      }

      return { ...prev, [id]: { ...toothData, [face]: selectedTool } };
    });
  };

  const ToolButton = ({ type, label, color, icon: Icon }: ToolButtonProps) => (
    <button 
      onClick={() => setSelectedTool(type)} 
      className={`w-full p-3 rounded-xl flex items-center gap-3 border transition-all duration-200 ${
        selectedTool === type 
          ? 'bg-gray-900 text-white border-gray-900 shadow-lg scale-[1.02]' 
          : 'bg-white border-gray-100 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
      }`}
    >
      <div className="w-6 h-6 rounded-lg flex items-center justify-center shadow-sm" style={{ backgroundColor: color }}>
         {Icon && <Icon size={14} className="text-white" />}
      </div>
      <span className="text-xs font-semibold">{label}</span>
    </button>
  );

  return (
    <div className="flex flex-col lg:flex-row h-screen bg-[#F8FAFC] overflow-hidden font-sans">
      
      <div className="flex-1 p-6 overflow-y-auto flex flex-col items-center">
        <header className="w-full flex justify-between items-center mb-8 max-w-6xl">
          <div>
             <h1 className="text-2xl font-extrabold text-gray-900 tracking-tight">Odontograma Digital</h1>
             <div className="flex items-center gap-3 mt-1">
                <span className="flex items-center gap-1.5 text-gray-500 text-xs bg-white px-2 py-1 rounded-md border border-gray-100 shadow-sm">
                  <User size={12} className="text-blue-500"/> {pacienteInfo.nome}
                </span>
                
                <div className="flex bg-gray-100 p-1 rounded-lg ml-4">
                  <button onClick={() => setViewMode('2d')} className={`px-3 py-1 rounded-md text-[10px] font-bold flex items-center gap-2 transition-all ${viewMode === '2d' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400'}`}>
                    <Layout size={12}/> 2D
                  </button>
                  <button onClick={() => setViewMode('3d')} className={`px-3 py-1 rounded-md text-[10px] font-bold flex items-center gap-2 transition-all ${viewMode === '3d' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400'}`}>
                    <Box size={12}/> 3D
                  </button>
                </div>
             </div>
          </div>
          <button 
            onClick={handleSalvarBanco}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2.5 rounded-xl flex items-center gap-2 hover:bg-blue-700 transition-all shadow-md hover:shadow-lg active:scale-95 text-xs font-bold disabled:opacity-50"
          >
            <Save size={16} /> {loading ? 'Salvando...' : 'Salvar Prontuário'}
          </button>
        </header>

        <div className="bg-white p-10 rounded-3xl shadow-xl shadow-blue-900/5 border border-gray-100 w-full max-w-6xl flex flex-col items-center relative overflow-hidden min-h-[600px]">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
            
            <div className="mb-10 flex flex-col items-center">
              <div className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest mb-4 flex items-center gap-2 ${
                selectedTool ? 'bg-blue-50 text-blue-600 border border-blue-100' : 'bg-gray-50 text-gray-400 border border-gray-100'
              }`}>
                  {selectedTool ? (
                    <><Activity size={10}/> Modo de Edição: {selectedTool.toUpperCase()}</>
                  ) : (
                    <><Info size={10}/> Selecione uma ferramenta ao lado</>
                  )}
              </div>
            </div>
            
            {viewMode === '2d' ? (
              <div className="space-y-12 py-4 animate-in fade-in duration-500">
                <div className="flex flex-col items-center">
                  <span className="text-[10px] font-bold text-gray-300 uppercase tracking-[0.2em] mb-6">Arcada Superior</span>
                  <div className="flex gap-2 justify-center flex-wrap">
                      {upperArcade.map(id => (
                        <GeometricTooth key={id} id={id} data={mouth[id] || {}} onFaceClick={handleToothClick} />
                      ))}
                  </div>
                </div>
                <div className="w-full h-px bg-gray-50 relative">
                  <div className="absolute inset-0 flex items-center justify-center"><div className="w-2 h-2 rounded-full bg-gray-200"></div></div>
                </div>
                <div className="flex flex-col items-center">
                  <div className="flex gap-2 justify-center flex-wrap mb-6">
                      {lowerArcade.map(id => (
                        <GeometricTooth key={id} id={id} data={mouth[id] || {}} onFaceClick={handleToothClick} />
                      ))}
                  </div>
                  <span className="text-[10px] font-bold text-gray-300 uppercase tracking-[0.2em]">Arcada Inferior</span>
                </div>
              </div>
            ) : (
              <div className="w-full h-full animate-in zoom-in-95 duration-500 p-4">
                 <Skull3D mouthData={mouth} onToothSelect={(id: number) => handleToothClick(id, 'oclusal')} />
                 <p className="text-center text-[10px] text-gray-400 mt-4">
                   * No modo 3D, clique nos dentes para aplicar o tratamento.
                 </p>
              </div>
            )}
        </div>
        
        <footer className="mt-8 text-gray-400 text-[10px] flex gap-6 flex-wrap justify-center">
           <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-500"></div> Cárie</div>
        </footer>
      </div>

      <aside className="w-full lg:w-80 bg-white border-l border-gray-100 p-6 shadow-2xl z-20 overflow-y-auto">
        <div className="space-y-3">
            <ToolButton type="caries" label="Cárie / Lesão" color="#ef4444" icon={AlertCircle} />
            <ToolButton type="restoration" label="Restauração" color="#3b82f6" icon={CheckCircle} />
            <ToolButton type="canal" label="Endodontia (Canal)" color="#22c55e" icon={Activity} />
            <ToolButton type="implant" label="Implante Dentário" color="#a855f7" icon={Activity} />
            <ToolButton type="extraction" label="Extração / Ausente" color="#1f2937" icon={Skull} />
            
            <div className="pt-6 mt-6 border-t border-gray-50">
              <button onClick={() => setSelectedTool(null)} className={`w-full p-3 rounded-xl flex items-center gap-3 border transition-all duration-200 ${selectedTool === null ? 'bg-gray-100 text-gray-900 border-gray-200 shadow-inner' : 'bg-white border-gray-100 text-gray-500 hover:bg-gray-50'}`}>
                  <div className="w-6 h-6 bg-white border border-gray-200 rounded-lg flex items-center justify-center"><Eraser size={14} className="text-gray-400" /></div>
                  <span className="text-xs font-semibold">Borracha / Limpar</span>
              </button>
            </div>
        </div>
      </aside>
    </div>
  );
}