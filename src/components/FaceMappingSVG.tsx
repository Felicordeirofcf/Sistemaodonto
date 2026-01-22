import React from 'react';

export type FaceZone = 
  | 'forehead' 
  | 'glabella' 
  | 'eyes_left' 
  | 'eyes_right' 
  | 'nose' 
  | 'malar_left' 
  | 'malar_right' 
  | 'lips' 
  | 'mandible_left' 
  | 'mandible_right' 
  | 'chin';

interface FaceMappingSVGProps {
  selectedZones: Set<FaceZone>;
  onZoneClick: (zone: FaceZone) => void;
}

export function FaceMappingSVG({ selectedZones, onZoneClick }: FaceMappingSVGProps) {
  const getZoneColor = (zone: FaceZone) => {
    return selectedZones.has(zone) ? 'rgba(59, 130, 246, 0.6)' : 'rgba(255, 255, 255, 0.1)';
  };

  const getStrokeColor = (zone: FaceZone) => {
    return selectedZones.has(zone) ? '#3b82f6' : '#d1d5db';
  };

  return (
    <div className="relative w-full max-w-md mx-auto aspect-[3/4] bg-gradient-to-b from-gray-50 to-white rounded-3xl shadow-inner p-4 border border-gray-100">
      <svg viewBox="0 0 200 260" className="w-full h-full drop-shadow-2xl">
        {/* Contorno da Face (Base) */}
        <path 
          d="M40,60 Q40,20 100,20 Q160,20 160,60 Q160,120 150,180 Q140,240 100,240 Q60,240 50,180 Q40,120 40,60" 
          fill="#fdf2f2" 
          stroke="#e5e7eb" 
          strokeWidth="2"
        />

        {/* Testa (Forehead) */}
        <path 
          d="M55,55 Q100,35 145,55 L140,85 Q100,75 60,85 Z" 
          fill={getZoneColor('forehead')} 
          stroke={getStrokeColor('forehead')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('forehead')}
        />

        {/* Glabela (Entre sobrancelhas) */}
        <path 
          d="M90,85 Q100,80 110,85 L105,105 Q100,100 95,105 Z" 
          fill={getZoneColor('glabella')} 
          stroke={getStrokeColor('glabella')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('glabella')}
        />

        {/* Olhos Esquerdo */}
        <path 
          d="M55,95 Q75,85 90,100 Q75,115 55,105 Z" 
          fill={getZoneColor('eyes_left')} 
          stroke={getStrokeColor('eyes_left')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('eyes_left')}
        />

        {/* Olhos Direito */}
        <path 
          d="M110,100 Q125,85 145,95 Q145,105 110,115 Z" 
          fill={getZoneColor('eyes_right')} 
          stroke={getStrokeColor('eyes_right')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('eyes_right')}
        />

        {/* Nariz */}
        <path 
          d="M95,105 L105,105 L115,150 Q100,160 85,150 Z" 
          fill={getZoneColor('nose')} 
          stroke={getStrokeColor('nose')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('nose')}
        />

        {/* Malar Esquerdo (Bochecha) */}
        <path 
          d="M50,120 Q70,120 85,150 L75,180 Q50,170 45,140 Z" 
          fill={getZoneColor('malar_left')} 
          stroke={getStrokeColor('malar_left')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('malar_left')}
        />

        {/* Malar Direito (Bochecha) */}
        <path 
          d="M150,120 Q130,120 115,150 L125,180 Q150,170 155,140 Z" 
          fill={getZoneColor('malar_right')} 
          stroke={getStrokeColor('malar_right')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('malar_right')}
        />

        {/* Lábios */}
        <path 
          d="M80,185 Q100,175 120,185 Q125,200 100,205 Q75,200 80,185" 
          fill={getZoneColor('lips')} 
          stroke={getStrokeColor('lips')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('lips')}
        />

        {/* Mandíbula Esquerda */}
        <path 
          d="M50,185 L70,215 L90,230 L55,210 Z" 
          fill={getZoneColor('mandible_left')} 
          stroke={getStrokeColor('mandible_left')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('mandible_left')}
        />

        {/* Mandíbula Direita */}
        <path 
          d="M150,185 L130,215 L110,230 L145,210 Z" 
          fill={getZoneColor('mandible_right')} 
          stroke={getStrokeColor('mandible_right')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('mandible_right')}
        />

        {/* Queixo (Chin) */}
        <path 
          d="M90,230 Q100,245 110,230 L105,215 Q100,210 95,215 Z" 
          fill={getZoneColor('chin')} 
          stroke={getStrokeColor('chin')} 
          strokeWidth="1.5"
          className="cursor-pointer transition-all hover:fill-blue-100"
          onClick={() => onZoneClick('chin')}
        />

        {/* Linhas de Expressão (Detalhes estéticos) */}
        <path d="M75,190 Q100,185 125,190" fill="none" stroke="#fecaca" strokeWidth="0.5" />
        <path d="M85,145 Q100,150 115,145" fill="none" stroke="#fecaca" strokeWidth="0.5" />
      </svg>

      {/* Legenda Flutuante */}
      <div className="absolute bottom-6 right-6 bg-white/80 backdrop-blur-sm p-3 rounded-2xl border border-gray-100 shadow-sm">
        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Face Mapping 2.0</p>
      </div>
    </div>
  );
}