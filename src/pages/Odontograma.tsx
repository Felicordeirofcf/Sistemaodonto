// @ts-nocheck
import { useState, useEffect } from 'react';
import { GeometricTooth } from '../components/GeometricTooth'; 
import { Save, User, Eraser, Search } from 'lucide-react';
import { Skull3D } from '../components/Skull3D';

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

export function Odontograma() {
  const [mouth, setMouth] = useState<Record<number, ToothState>>({});
  const [selectedTool, setSelectedTool] = useState<TreatmentType>(null);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  
  const [listaPacientes, setListaPacientes] = useState<any[]>([]);
  const [pacienteId, setPacienteId] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const upperArcade = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lowerArcade = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  useEffect(() => {
    fetch('/api/patients', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
    .then(res => res.json())
    .then(data => {
      if (Array.isArray(data)) setListaPacientes(data);
    })
    .catch(console.error);
  }, []);

  const handleSelectPatient = (id: string) => {
    setPacienteId(id);
    const paciente = listaPacientes.find(p => p.id === parseInt(id));
    // CORREÇÃO: Inicialização segura do odontograma_data
    if (paciente && paciente.odontogram_data) {
      setMouth(paciente.odontogram_data);
    } else {
      setMouth({}); 
    }
  };

  const handleSave = async () => {
    if (!pacienteId) return alert("Selecione um paciente primeiro!");
    
    setLoading(true);
    try {
      const response = await fetch(`/api/patients/${pacienteId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        },
        body: JSON.stringify({ odontogram_data: mouth })
      });
      
      if (!response.ok) throw new Error();
      alert("Odontograma salvo com sucesso!");
    } catch (error) {
      alert("Erro ao salvar.");
    } finally {
      setLoading(false);
    }
  };

  const handleToothClick = (toothId: number, face: ToothFace) => {
    // CORREÇÃO: Impedir ações se nenhum paciente estiver selecionado
    if (!pacienteId) return;

    setMouth(prev => {
      const toothState = prev[toothId] || {};
      
      if (selectedTool === null) {
        const newState = { ...toothState };
        delete newState[face];
        return { ...prev, [toothId]: newState };
      }

      return {
        ...prev,
        [toothId]: { ...toothState, [face]: selectedTool }
      };
    });
  };

  const AlertCircleIcon = () => <div className="w-3 h-3 rounded-full border border-current" />;
  const BoxIcon = () => <div className="w-3 h-3 border border-current" />;
  const ActivityIcon = () => <div className="w-3 h-3 border-b-2 border-current" />;
  const ScrewIcon = () => <div className="w-1 h-3 bg-current" />;

  const tools: ToolButtonProps[] = [
    { type: 'caries', label: 'Cárie', color: 'bg-red-500', icon: AlertCircleIcon },
    { type: 'restoration', label: 'Restauração', color: 'bg-blue-500', icon: BoxIcon },
    { type: 'canal', label: 'Canal', color: 'bg-purple-500', icon: ActivityIcon },
    { type: 'extraction', label: 'Extração', color: 'bg-gray-800', icon: Eraser },
    { type: 'implant', label: 'Implante', color: 'bg-green-500', icon: ScrewIcon },
  ];

  return (
    <div className="p-8 h-full flex flex-col">
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 border border-gray-200 rounded-lg px-3 py-2 bg-gray-50">
                <User size={20} className="text-gray-400" />
                <select 
                    className="bg-transparent outline-none text-gray-700 min-w-[200px]"
                    value={pacienteId}
                    onChange={(e) => handleSelectPatient(e.target.value)}
                >
                    <option value="">Selecione um Paciente...</option>
                    {listaPacientes.map(p => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                </select>
            </div>
        </div>

        <div className="flex gap-2">
            <div className="flex bg-gray-100 p-1 rounded-lg">
                <button onClick={() => setViewMode('2d')} className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${viewMode === '2d' ? 'bg-white shadow text-blue-600' : 'text-gray-500'}`}>2D</button>
                <button onClick={() => setViewMode('3d')} className={`px-4 py-2 rounded-md text-sm font-bold transition-all ${viewMode === '3d' ? 'bg-white shadow text-blue-600' : 'text-gray-500'}`}>3D</button>
            </div>
            
            <button 
                onClick={handleSave}
                disabled={loading || !pacienteId}
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
                <Save size={18} /> {loading ? 'Salvando...' : 'Salvar'}
            </button>
        </div>
      </div>

      <div className="flex gap-6 flex-1 h-full overflow-hidden">
        <div className="w-64 bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col gap-3 h-fit">
          <h3 className="font-bold text-gray-700 mb-2">Ferramentas</h3>
          {tools.map((tool) => (
            <button
              key={tool.type}
              onClick={() => setSelectedTool(tool.type)}
              className={`flex items-center gap-3 p-3 rounded-lg transition-all border ${selectedTool === tool.type ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-transparent hover:bg-gray-50 text-gray-600'}`}
            >
              <div className={`w-8 h-8 rounded-lg ${tool.color} flex items-center justify-center text-white shadow-sm`}>
                <tool.icon size={16} />
              </div>
              <span className="font-medium">{tool.label}</span>
            </button>
          ))}
          <button
              onClick={() => setSelectedTool(null)}
              className={`flex items-center gap-3 p-3 rounded-lg transition-all border ${selectedTool === null ? 'border-red-500 bg-red-50 text-red-700' : 'border-transparent hover:bg-gray-50 text-gray-600'}`}
            >
              <div className="w-8 h-8 rounded-lg bg-white border-2 border-gray-300 flex items-center justify-center text-gray-500">
                <Eraser size={16} />
              </div>
              <span className="font-medium">Borracha</span>
            </button>
        </div>

        <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 relative overflow-y-auto p-8 flex justify-center">
            {!pacienteId && (
                <div className="absolute inset-0 bg-white/80 z-10 flex flex-col items-center justify-center text-gray-400">
                    <User size={64} className="mb-4 opacity-20" />
                    <p className="text-xl font-medium">Selecione um paciente acima para começar</p>
                </div>
            )}

            {viewMode === '2d' ? (
                <div className="max-w-3xl w-full flex flex-col gap-12 py-10">
                    <div className="flex justify-center gap-2 flex-wrap">
                        {upperArcade.map(id => (
                            <GeometricTooth 
                              key={id} 
                              id={id} 
                              state={mouth?.[id] || {}} 
                              onClick={handleToothClick} 
                            />
                        ))}
                    </div>
                    <div className="flex justify-center gap-2 flex-wrap">
                        {lowerArcade.map(id => (
                            <GeometricTooth 
                              key={id} 
                              id={id} 
                              state={mouth?.[id] || {}} 
                              onClick={handleToothClick} 
                            />
                        ))}
                    </div>
                </div>
            ) : (
                <div className="w-full h-full flex items-center justify-center">
                    {/* CORREÇÃO: Passando mouthData e onToothSelect com fallback para evitar o erro undefined */}
                    <Skull3D mouthData={mouth || {}} onToothSelect={(id) => console.log(id)} />
                </div>
            )}
        </div>
      </div>
    </div>
  );
}