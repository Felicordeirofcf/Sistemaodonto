// @ts-nocheck
// Removido import de React para evitar conflitos em ambientes Vite/Build modernos

export type ToothFace = 'occlusal' | 'vestibular' | 'lingual' | 'mesial' | 'distal';

export type ToothState = {
  [key in ToothFace]?: string; 
};

interface GeometricToothProps {
  id: number;
  state: ToothState; // Alterado de 'data' para 'state' para casar com a chamada no Odontograma
  onClick: (id: number, face: ToothFace) => void; // Ajustado para receber (id, face)
}

export function GeometricTooth({ id, state = {}, onClick }: GeometricToothProps) {
  
  const getColor = (face: ToothFace) => {
    // Defesa contra estado indefinido
    const status = state && state[face] ? state[face] : null;
    
    switch (status) {
      case 'caries': return '#ef4444'; // Vermelho
      case 'restoration': return '#3b82f6'; // Azul
      case 'canal': return '#22c55e'; // Verde
      case 'extraction': return '#1f2937'; // Preto
      case 'implant': return '#a855f7'; // Roxo
      default: return 'white'; // Branco
    }
  };

  // Handler interno para garantir que o clique passe os parâmetros corretos ao pai
  const handleFaceClick = (face: ToothFace) => {
    if (onClick) {
      onClick(id, face);
    }
  };

  return (
    <div className="flex flex-col items-center gap-1 group">
      <div className="relative w-12 h-12 cursor-pointer transition-transform hover:scale-110">
        <svg viewBox="0 0 100 100" className="drop-shadow-sm filter">
          {/* Faces do Dente */}
          <polygon points="0,0 100,0 70,30 30,30" fill={getColor('vestibular')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => handleFaceClick('vestibular')} />
          <polygon points="30,70 70,70 100,100 0,100" fill={getColor('lingual')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => handleFaceClick('lingual')} />
          <polygon points="0,0 30,30 30,70 0,100" fill={getColor('distal')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => handleFaceClick('distal')} />
          <polygon points="100,0 70,30 70,70 100,100" fill={getColor('mesial')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => handleFaceClick('mesial')} />
          <rect x="30" y="30" width="40" height="40" fill={getColor('occlusal')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => handleFaceClick('occlusal')} />
        </svg>
        
        {/* Marcador de Extração (X) */}
        {state && Object.values(state).includes('extraction') && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span className="text-4xl text-red-600 font-bold opacity-80 select-none">X</span>
            </div>
        )}
      </div>
      <span className="text-[10px] font-bold text-gray-400">{id}</span>
    </div>
  );
}