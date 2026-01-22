// --- REMOVI O IMPORT DO REACT QUE DAVA ERRO ---
export type ToothFace = 'occlusal' | 'vestibular' | 'lingual' | 'mesial' | 'distal';

export type ToothState = {
  [key in ToothFace]?: string; 
};

interface GeometricToothProps {
  id: number;
  data: ToothState;
  onFaceClick: (face: ToothFace) => void;
}

export function GeometricTooth({ id, data, onFaceClick }: GeometricToothProps) {
  
  const getColor = (face: ToothFace) => {
    const status = data[face];
    switch (status) {
      case 'caries': return '#ef4444'; // Vermelho
      case 'restoration': return '#3b82f6'; // Azul
      case 'canal': return '#22c55e'; // Verde
      case 'extraction': return '#1f2937'; // Preto
      case 'implant': return '#a855f7'; // Roxo
      default: return 'white'; // Branco
    }
  };

  return (
    <div className="flex flex-col items-center gap-1 group">
      <div className="relative w-12 h-12 cursor-pointer transition-transform hover:scale-110">
        <svg viewBox="0 0 100 100" className="drop-shadow-sm filter">
          {/* Faces do Dente */}
          <polygon points="0,0 100,0 70,30 30,30" fill={getColor('vestibular')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => onFaceClick('vestibular')} />
          <polygon points="30,70 70,70 100,100 0,100" fill={getColor('lingual')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => onFaceClick('lingual')} />
          <polygon points="0,0 30,30 30,70 0,100" fill={getColor('distal')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => onFaceClick('distal')} />
          <polygon points="100,0 70,30 70,70 100,100" fill={getColor('mesial')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => onFaceClick('mesial')} />
          <rect x="30" y="30" width="40" height="40" fill={getColor('occlusal')} stroke="#9ca3af" strokeWidth="1" className="hover:opacity-80 transition-opacity" onClick={() => onFaceClick('occlusal')} />
        </svg>
        
        {Object.values(data).includes('extraction') && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span className="text-4xl text-red-600 font-bold opacity-80">X</span>
            </div>
        )}
      </div>
      <span className="text-xs font-bold text-gray-500">{id}</span>
    </div>
  );
}