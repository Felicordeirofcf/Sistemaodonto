import React, { useState, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, ContactShadows, Float } from '@react-three/drei';
import * as THREE from 'three';

// --- CORREÇÃO: Tipos definidos localmente para evitar erro de importação ---
type TreatmentType = 'caries' | 'restoration' | 'canal' | 'extraction' | 'implant' | null;

export interface ToothState {
  [key: string]: TreatmentType;
}
// --------------------------------------------------------------------------

// Interface para as props
interface Skull3DProps {
  mouthData: Record<number, ToothState>;
  onToothSelect: (id: number) => void;
}

// Componente para um dente com formato anatômico (Coroa + Raiz)
function AnatomicalTooth({ position, rotation, id, onSelect, color = "white", isUpper = true }: any) {
  const [hovered, setHover] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const meshRef = useRef<THREE.Group>(null);

  // Cores baseadas no status
  const getMaterialColor = () => {
    if (hovered) return "#60a5fa"; // Azul claro no hover
    return color;
  };

  return (
    <group 
      position={position} 
      rotation={rotation}
      onPointerOver={(e) => { e.stopPropagation(); setHover(true); }}
      onPointerOut={() => setHover(false)}
      onClick={(e) => { e.stopPropagation(); onSelect(id); }}
    >
      {/* Coroa do Dente (Parte visível) */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[0.35, 0.4, 0.35]} />
        <meshStandardMaterial 
          color={getMaterialColor()} 
          roughness={0.05} 
          metalness={0.1} 
          emissive={hovered ? "#1e40af" : "#000000"}
          emissiveIntensity={0.2}
        />
      </mesh>
      
      {/* Raiz do Dente (Parte afilada) */}
      <mesh position={[0, isUpper ? 0.3 : -0.3, 0]}>
        <cylinderGeometry args={[0.15, 0.02, 0.5, 8]} />
        <meshStandardMaterial 
          color={getMaterialColor()} 
          roughness={0.3} 
          opacity={0.8} 
          transparent 
        />
      </mesh>

      {/* Brilho sutil no topo da coroa */}
      <mesh position={[0, isUpper ? -0.2 : 0.2, 0]}>
        <sphereGeometry args={[0.18, 16, 16]} />
        <meshStandardMaterial color="white" opacity={0.3} transparent />
      </mesh>
    </group>
  );
}

function SkullModel({ onToothSelect, mouthData }: any) {
  const upperTeeth = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lowerTeeth = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  const getToothColor = (id: number) => {
    const data = mouthData[id];
    if (!data) return "#f8fafc"; // Branco perolado
    
    // Verifica os valores do objeto de faces
    // Cast para garantir que o TypeScript entenda que são TreatmentTypes
    const treatments = Object.values(data) as TreatmentType[];
    
    if (treatments.includes('extraction')) return "#1f2937";
    if (treatments.includes('caries')) return "#ef4444";
    if (treatments.includes('restoration')) return "#3b82f6";
    if (treatments.includes('canal')) return "#22c55e";
    if (treatments.includes('implant')) return "#a855f7";
    
    return "#f8fafc";
  };

  return (
    <group>
      {/* Base do Crânio Estilizada */}
      <mesh position={[0, 0.5, -0.8]}>
        <sphereGeometry args={[2.5, 64, 64]} />
        <meshStandardMaterial 
          color="#e2e8f0" 
          transparent 
          opacity={0.1} 
          wireframe={false}
          roughness={0}
        />
      </mesh>

      {/* Arcada Superior */}
      <group position={[0, 0.5, 0]}>
        {upperTeeth.map((id, i) => {
          const angle = (i / (upperTeeth.length - 1)) * Math.PI - Math.PI / 2;
          const radiusX = 2.0;
          const radiusZ = 1.8;
          const x = Math.cos(angle) * radiusX;
          const z = Math.sin(angle) * radiusZ;
          return (
            <AnatomicalTooth 
              key={id} 
              id={id} 
              position={[x, 0, z]} 
              rotation={[0, -angle + Math.PI/2, 0]}
              onSelect={onToothSelect} 
              color={getToothColor(id)}
              isUpper={true}
            />
          );
        })}
      </group>

      {/* Arcada Inferior */}
      <group position={[0, -0.5, 0]}>
        {lowerTeeth.map((id, i) => {
          const angle = (i / (lowerTeeth.length - 1)) * Math.PI - Math.PI / 2;
          const radiusX = 1.9;
          const radiusZ = 1.7;
          const x = Math.cos(angle) * radiusX;
          const z = Math.sin(angle) * radiusZ;
          return (
            <AnatomicalTooth 
              key={id} 
              id={id} 
              position={[x, 0, z]} 
              rotation={[0, -angle + Math.PI/2, 0]}
              onSelect={onToothSelect} 
              color={getToothColor(id)}
              isUpper={false}
            />
          );
        })}
      </group>
    </group>
  );
}

export function Skull3D({ onToothSelect, mouthData }: Skull3DProps) {
  return (
    <div className="w-full h-[500px] bg-[#fdfdfd] rounded-[2.5rem] border border-gray-100 shadow-2xl overflow-hidden relative group">
      {/* Overlay de Interface */}
      <div className="absolute top-6 left-6 z-10 flex flex-col gap-2 pointer-events-none">
        <span className="px-4 py-1.5 bg-white/90 backdrop-blur-md text-blue-600 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] border border-blue-50 shadow-xl">
          Precision 3D Engine
        </span>
        <div className="flex gap-2 items-center">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
          <span className="text-[9px] text-gray-400 font-bold uppercase tracking-widest">Live Sync Active</span>
        </div>
      </div>
      
      <Canvas shadows dpr={[1, 2]}>
        <PerspectiveCamera makeDefault position={[0, 3, 8]} fov={40} />
        <OrbitControls 
          enablePan={false} 
          minDistance={5} 
          maxDistance={12}
          makeDefault
          autoRotate={false}
        />
        
        <ambientLight intensity={0.7} />
        <spotLight position={[10, 15, 10]} angle={0.3} penumbra={1} intensity={2} castShadow />
        <pointLight position={[-10, -10, -10]} color="blue" intensity={0.5} />
        <directionalLight position={[0, 5, 5]} intensity={0.5} />
        
        <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
          <SkullModel onToothSelect={onToothSelect} mouthData={mouthData} />
        </Float>
        
        <Environment preset="apartment" />
        <ContactShadows 
          position={[0, -2.5, 0]} 
          opacity={0.25} 
          scale={15} 
          blur={2.5} 
          far={5} 
        />
      </Canvas>

      {/* Controles de Navegação */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-4 bg-white/80 backdrop-blur-xl px-6 py-3 rounded-2xl border border-white/50 shadow-2xl opacity-0 group-hover:opacity-100 transition-all duration-500 translate-y-4 group-hover:translate-y-0 pointer-events-none">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-gray-300"></div>
          <span className="text-[9px] font-bold text-gray-500 uppercase">Orbit</span>
        </div>
        <div className="w-px h-3 bg-gray-200"></div>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-gray-300"></div>
          <span className="text-[9px] font-bold text-gray-500 uppercase">Zoom</span>
        </div>
      </div>
    </div>
  );
}