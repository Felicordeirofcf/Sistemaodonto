// @ts-nocheck
import { useState, useEffect } from 'react';
import { GeometricTooth } from '../components/GeometricTooth'; 
import { Save, User, Eraser, Loader2 } from 'lucide-react';
import { Skull3D } from '../components/Skull3D';
import { AlertCircle } from 'lucide-react';

export type ToothFace = 'vestibular' | 'lingual' | 'distal' | 'mesial' | 'oclusal' | 'occlusal';
export type TreatmentType = 'caries' | 'restoration' | 'canal' | 'extraction' | 'implant' | null;

export function Odontograma() {
  const [mouth, setMouth] = useState<Record<number, ToothState>>({});
  const [selectedTool, setSelectedTool] = useState<TreatmentType>(null);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  
  const [listaPacientes, setListaPacientes] = useState<any[]>([]);
  const [pacienteId, setPacienteId] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const upperArcade = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lowerArcade = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  // Busca pacientes garantindo autorização
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
    
    // CORREÇÃO: Mapeamento seguro do odontograma vindo do banco
    if (paciente && paciente.odontogram_data) {
      // Se os dados vierem como string (JSON), fazemos o parse
      const data = typeof paciente.odontogram_data === 'string' 
        ? JSON.parse(paciente.odontogram_data) 
        : paciente.odontogram_data;
      setMouth(data);
    } else {
      setMouth({}); 
    }
  };

  const handleSave = async () => {
    if (!pacienteId) return;
    
    setLoading(true);
    try {
      // CORREÇÃO: Rota unificada PUT para evitar erro 405
      const response = await fetch(`/api/patients/${pacienteId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        },
        body: JSON.stringify({ odontogram_data: mouth })
      });
      
      if (!response.ok) throw new Error("Erro na resposta do servidor");
      alert("Odontograma salvo com sucesso!");
    } catch (error) {
      console.error("Erro ao salvar:", error);
      alert("Erro ao salvar alterações.");
    } finally {
      setLoading(false);
    }
  };

  const handleToothClick = (toothId: number, face: ToothFace) => {
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

  const tools = [
    { type: 'caries', label: 'Cárie', color: 'bg-red-500', icon: AlertCircleIcon },
    { type: 'restoration', label: 'Restauração', color: 'bg-blue-500', icon: BoxIcon },
    { type: 'canal', label: 'Canal', color: 'bg-purple-500', icon: ActivityIcon },
    { type: 'extraction', label: 'Extração', color: 'bg-gray-800', icon: Eraser },
    { type: 'implant', label: 'Implante', color: 'bg-green-500', icon: ScrewIcon },
  ];

  return (
    <div className="p-8 h-full flex flex-col bg-gray-50">
      <header className="bg-white p-6 rounded-[2rem] shadow-sm border border-gray-100 mb-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 border border-gray-100 rounded-2xl px-4 py-2 bg-gray-50 focus-within:ring-2 focus-within:ring-blue-500 transition-all">
                <User size={20} className="text-gray-400" />
                <select 
                    className="bg-transparent outline-none text-gray-700 min-w-[250px] font-bold text-sm"
                    value={pacienteId}
                    onChange={(e) => handleSelectPatient(e.target.value)}
                >
                    <option value="">Selecione um Paciente...</option>
                    {listaPacientes.map(p => (
                        // CORREÇÃO: Fallback para garantir que o nome apareça
                        <option key={p.id} value={p.id}>{p.name || p.nome || "Paciente sem nome"}</option>
                    ))}
                </select>
            </div>
        </div>

        <div className="flex gap-4">
            <div className="flex bg-gray-100 p-1.5 rounded-2xl">
                <button onClick={() => setViewMode('2d')} className={`px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${viewMode === '2d' ? 'bg-white shadow-lg text-blue-600' : 'text-gray-400'}`}>2D</button>
                <button onClick={() => setViewMode('3d')} className={`px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${viewMode === '3d' ? 'bg-white shadow-lg text-blue-600' : 'text-gray-400'}`}>3D</button>
            </div>
            
            <button 
                onClick={handleSave}
                disabled={loading || !pacienteId}
                className="flex items-center gap-2 bg-blue-600 text-white px-8 py-2 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-blue-700 disabled:opacity-50 shadow-xl shadow-blue-100 transition-all active:scale-95"
            >
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                {loading ? 'Salvando...' : 'Salvar'}
            </button>
        </div>
      </header>

      <div className="flex gap-8 flex-1 overflow-hidden">
        {/* Painel de Ferramentas - UI Industrial */}
        <aside className="w-72 bg-white p-6 rounded-[2.5rem] shadow-sm border border-gray-100 flex flex-col gap-4 h-fit">
          <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Ferramentas de Exame</h3>
          {tools.map((tool) => (
            <button
              key={tool.type}
              onClick={() => setSelectedTool(tool.type)}
              className={`flex items-center gap-4 p-4 rounded-2xl transition-all border-2 ${selectedTool === tool.type ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-transparent hover:bg-gray-50 text-gray-600'}`}
            >
              <div className={`w-10 h-10 rounded-xl ${tool.color} flex items-center justify-center text-white shadow-lg shadow-gray-200`}>
                <tool.icon size={20} />
              </div>
              <span className="font-bold text-sm tracking-tight">{tool.label}</span>
            </button>
          ))}
          <button
              onClick={() => setSelectedTool(null)}
              className={`flex items-center gap-4 p-4 rounded-2xl transition-all border-2 mt-4 ${selectedTool === null ? 'border-red-500 bg-red-50 text-red-700' : 'border-transparent hover:bg-gray-50 text-gray-400 font-bold'}`}
            >
              <div className="w-10 h-10 rounded-xl bg-white border-2 border-gray-100 flex items-center justify-center text-gray-400">
                <Eraser size={20} />
              </div>
              <span className="text-sm">Borracha</span>
          </button>
        </aside>

        {/* Área Principal do Odontograma */}
        <main className="flex-1 bg-white rounded-[3rem] shadow-sm border border-gray-100 relative overflow-y-auto p-12 flex justify-center min-h-[500px]">
            {!pacienteId && (
                <div className="absolute inset-0 bg-white/90 z-20 backdrop-blur-sm flex flex-col items-center justify-center text-gray-300">
                    <User size={80} className="mb-6 opacity-10" />
                    <p className="text-xl font-black uppercase tracking-widest">Selecione um paciente para iniciar</p>
                </div>
            )}

            {viewMode === '2d' ? (
                <div className="max-w-4xl w-full flex flex-col gap-16 py-10 animate-in fade-in duration-500">
                    <div className="flex justify-center gap-3 flex-wrap">
                        {upperArcade.map(id => (
                            <GeometricTooth key={id} id={id} state={mouth?.[id] || {}} onClick={handleToothClick} />
                        ))}
                    </div>
                    <div className="flex justify-center gap-3 flex-wrap">
                        {lowerArcade.map(id => (
                            <GeometricTooth key={id} id={id} state={mouth?.[id] || {}} onClick={handleToothClick} />
                        ))}
                    </div>
                </div>
            ) : (
                <div className="w-full h-full min-h-[500px] flex items-center justify-center">
                    <Skull3D mouthData={mouth || {}} onToothSelect={(id) => console.log("Dente selecionado no 3D:", id)} />
                </div>
            )}
        </main>
      </div>
    </div>
  );
}

// Subcomponentes de ícone para as ferramentas
const AlertCircleIcon = ({size}: {size: number}) => <AlertCircle size={size} />;
const BoxIcon = ({size}: {size: number}) => <div className={`w-${size/4} h-${size/4} border-2 border-current rounded-sm`} />;
const ActivityIcon = ({size}: {size: number}) => <Clock size={size} />;
const ScrewIcon = ({size}: {size: number}) => <Activity size={size} />;