// @ts-nocheck
import React, { useState, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, ContactShadows, Float } from '@react-three/drei';
import * as THREE from 'three';

type TreatmentType = 'caries' | 'restoration' | 'canal' | 'extraction' | 'implant' | null;

export interface ToothState {
  [key: string]: TreatmentType;
}

interface Skull3DProps {
  mouthData: Record<number, ToothState>;
  onToothSelect: (id: number) => void;
}

function AnatomicalTooth({ position, rotation, id, onSelect, color = "white", isUpper = true }: any) {
  const [hovered, setHover] = useState(false);

  const getMaterialColor = () => {
    if (hovered) return "#60a5fa"; 
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
      
      <mesh position={[0, isUpper ? 0.3 : -0.3, 0]}>
        <cylinderGeometry args={[0.15, 0.02, 0.5, 8]} />
        <meshStandardMaterial 
          color={getMaterialColor()} 
          roughness={0.3} 
          opacity={0.8} 
          transparent 
        />
      </mesh>
    </group>
  );
}

function SkullModel({ onToothSelect, mouthData = {} }: any) {
  const upperTeeth = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
  const lowerTeeth = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

  const getToothColor = (id: number) => {
    // --- CORREÇÃO: Optional Chaining e Fallback para evitar erro 'undefined' ---
    const data = mouthData?.[id] || {}; 
    
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
      {/* Arcada Superior */}
      <group position={[0, 0.5, 0]}>
        {upperTeeth.map((id, i) => {
          const angle = (i / (upperTeeth.length - 1)) * Math.PI - Math.PI / 2;
          const x = Math.cos(angle) * 2.0;
          const z = Math.sin(angle) * 1.8;
          return (
            <AnatomicalTooth 
              key={id} id={id} 
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
          const x = Math.cos(angle) * 1.9;
          const z = Math.sin(angle) * 1.7;
          return (
            <AnatomicalTooth 
              key={id} id={id} 
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

export function Skull3D({ onToothSelect, mouthData = {} }: Skull3DProps) {
  return (
    <div className="w-full h-[500px] bg-[#fdfdfd] rounded-[2.5rem] border border-gray-100 shadow-2xl overflow-hidden relative">
      <Canvas shadows dpr={[1, 2]}>
        <PerspectiveCamera makeDefault position={[0, 3, 8]} fov={40} />
        <OrbitControls enablePan={false} minDistance={5} maxDistance={12} />
        <ambientLight intensity={0.7} />
        <spotLight position={[10, 15, 10]} angle={0.3} intensity={2} castShadow />
        
        <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
          {/* Fallback de objeto vazio passado aqui também por segurança */}
          <SkullModel onToothSelect={onToothSelect} mouthData={mouthData || {}} />
        </Float>
        
        <Environment preset="apartment" />
        <ContactShadows position={[0, -2.5, 0]} opacity={0.25} scale={15} blur={2.5} far={5} />
      </Canvas>
    </div>
  );
}