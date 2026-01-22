import React from 'react';

export type ToothFace = 'occlusal' | 'vestibular' | 'lingual' | 'mesial' | 'distal';

export type ToothState = {
  [key in ToothFace]?: string;
};

interface ToothSVGProps {
  id: number;
  data: ToothState;
  onFaceClick: (face: ToothFace) => void;
}

export function ToothSVG({ id, data, onFaceClick }: ToothSVGProps) {
  const getColor = (face: ToothFace) => {
    const status = data[face];
    switch (status) {
      case 'caries': return '#ef4444'; // Vermelho
      case 'restoration': return '#3b82f6'; // Azul
      case 'canal': return '#22c55e'; // Verde
      case 'extraction': return '#1f2937'; // Preto
      case 'implant': return '#a855f7'; // Roxo
      default: return '#ffffff'; // Branco
    }
  };

  const isExtracted = Object.values(data).includes('extraction');

  return (
    <div className="flex flex-col items-center gap-1 group">
      <div className="relative w-14 h-14 cursor-pointer transition-all duration-200 hover:scale-110">
        <svg viewBox="0 0 100 100" className={`w-full h-full drop-shadow-md ${isExtracted ? 'opacity-30' : ''}`}>
          {/* Definição de Sombra e Gradientes */}
          <defs>
            <filter id="innerShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="3" result="blur" />
              <feOffset dx="2" dy="2" />
              <feComposite in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1" result="shadow" />
              <feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.2 0" />
            </filter>
          </defs>

          {/* Face Vestibular (Topo) */}
          <path
            d="M20,20 L80,20 L70,35 L30,35 Z"
            fill={getColor('vestibular')}
            stroke="#d1d5db"
            strokeWidth="1.5"
            className="hover:brightness-90 transition-all"
            onClick={() => onFaceClick('vestibular')}
          />

          {/* Face Lingual (Base) */}
          <path
            d="M30,65 L70,65 L80,80 L20,80 Z"
            fill={getColor('lingual')}
            stroke="#d1d5db"
            strokeWidth="1.5"
            className="hover:brightness-90 transition-all"
            onClick={() => onFaceClick('lingual')}
          />

          {/* Face Distal (Esquerda) */}
          <path
            d="M20,20 L30,35 L30,65 L20,80 Z"
            fill={getColor('distal')}
            stroke="#d1d5db"
            strokeWidth="1.5"
            className="hover:brightness-90 transition-all"
            onClick={() => onFaceClick('distal')}
          />

          {/* Face Mesial (Direita) */}
          <path
            d="M80,20 L70,35 L70,65 L80,80 Z"
            fill={getColor('mesial')}
            stroke="#d1d5db"
            strokeWidth="1.5"
            className="hover:brightness-90 transition-all"
            onClick={() => onFaceClick('mesial')}
          />

          {/* Face Oclusal (Centro) */}
          <rect
            x="30"
            y="35"
            width="40"
            height="30"
            fill={getColor('occlusal')}
            stroke="#d1d5db"
            strokeWidth="1.5"
            className="hover:brightness-90 transition-all"
            onClick={() => onFaceClick('occlusal')}
          />

          {/* Contorno Anatômico do Dente */}
          <path
            d="M15,15 Q50,5 85,15 Q95,50 85,85 Q50,95 15,85 Q5,50 15,15 Z"
            fill="none"
            stroke="#9ca3af"
            strokeWidth="2"
            pointerEvents="none"
          />
        </svg>

        {isExtracted && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <line x1="20" y1="20" x2="80" y2="80" stroke="#ef4444" strokeWidth="8" strokeLinecap="round" />
              <line x1="80" y1="20" x2="20" y2="80" stroke="#ef4444" strokeWidth="8" strokeLinecap="round" />
            </svg>
          </div>
        )}
      </div>
      <span className={`text-[10px] font-bold ${isExtracted ? 'text-red-400' : 'text-gray-400'}`}>{id}</span>
    </div>
  );
}