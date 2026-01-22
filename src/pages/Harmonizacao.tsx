import { useState } from 'react';
import { Syringe, Save, Eraser, Sparkles, DollarSign, Info } from 'lucide-react';

type Zone = 'forehead' | 'glabella' | 'crowsFeet' | 'cheeks' | 'lips' | 'chin' | 'jaw' | 'nasolabial';

interface ProcedureData {
  units: number;
  product: 'toxin' | 'filler' | 'threads';
  price: number;
}

interface FaceMapState {
  [key: string]: ProcedureData;
}

export function Harmonizacao() {
  const [procedures, setProcedures] = useState<FaceMapState>({});
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);

  const PRICES = { toxin: 45, filler: 900, threads: 250 };

  const handleAdd = (zone: Zone, type: 'toxin' | 'filler') => {
    setProcedures(prev => {
      const current = prev[zone] || { units: 0, product: type, price: 0 };
      const increment = type === 'filler' ? 1 : 2;
      const newUnits = current.units + increment;
      const newPrice = newUnits * (type === 'filler' ? PRICES.filler : PRICES.toxin);
      return { ...prev, [zone]: { units: newUnits, product: type, price: newPrice } };
    });
    setSelectedZone(zone);
  };

  const handleClearZone = (zone: Zone) => {
    setProcedures(prev => {
      const newState = { ...prev };
      delete newState[zone];
      return newState;
    });
    setSelectedZone(null);
  };

  const calculateTotal = () => Object.values(procedures).reduce((acc, curr) => acc + curr.price, 0);

  const FaceZone = ({ zone, d }: { zone: Zone, d: string }) => {
    const data = procedures[zone];
    const isSelected = selectedZone === zone;
    const hasProduct = !!data;
    const fillColor = data?.product === 'toxin' ? 'fill-purple-200' : 'fill-pink-200';
    const strokeColor = data?.product === 'toxin' ? 'stroke-purple-500' : 'stroke-pink-500';

    return (
      <g onClick={() => setSelectedZone(zone)} className="cursor-pointer group transition-all duration-300">
        <path d={d} className={`transition-all duration-500 ease-in-out ${hasProduct ? `${fillColor} ${strokeColor} opacity-90` : 'fill-transparent stroke-transparent hover:fill-blue-50/50 hover:stroke-blue-200'} ${isSelected ? 'stroke-[2px] filter drop-shadow-md' : 'stroke-[1px]'}`} />
        {hasProduct && <foreignObject x="0" y="0" width="100%" height="100%" className="pointer-events-none overflow-visible"></foreignObject>}
      </g>
    );
  };

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-50 overflow-hidden font-sans text-sm">
      
      {/* MAPA VISUAL (Centro) */}
      <div className="flex-1 p-4 overflow-y-auto flex flex-col items-center relative custom-scrollbar justify-center">
        
        <div className="absolute top-4 left-4 z-10 bg-white/80 backdrop-blur px-3 py-1.5 rounded-full border border-gray-100 shadow-sm">
          <h1 className="text-sm font-bold text-gray-800 flex items-center gap-2">
            <Sparkles className="text-purple-500 w-4 h-4" /> Face Mapping 3D
          </h1>
        </div>

        {/* Reduzi o max-w para 340px para ficar mais delicado */}
        <div className="relative w-full max-w-[340px] aspect-[3/4.2]">
          <svg viewBox="0 0 400 550" className="w-full h-full drop-shadow-xl">
            <defs>
              <linearGradient id="skinGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#fffcf9" />
                <stop offset="100%" stopColor="#fcefe9" />
              </linearGradient>
            </defs>
            <g className="pointer-events-none">
                <path d="M70,150 C70,50 330,50 330,150 C330,280 300,400 200,480 C100,400 70,280 70,150 Z" fill="url(#skinGradient)" stroke="#e2d5ce" strokeWidth="2" />
                <path d="M130,460 Q130,520 100,550 M270,460 Q270,520 300,550" fill="none" stroke="#e2d5ce" strokeWidth="2" />
                <path d="M120,135 Q150,120 180,135" fill="none" stroke="#bcaaa4" strokeWidth="3" strokeLinecap="round" />
                <path d="M220,135 Q250,120 280,135" fill="none" stroke="#bcaaa4" strokeWidth="3" strokeLinecap="round" />
                <path d="M130,165 Q150,185 170,165" fill="none" stroke="#a1887f" strokeWidth="2" strokeLinecap="round" />
                <path d="M230,165 Q250,185 270,165" fill="none" stroke="#a1887f" strokeWidth="2" strokeLinecap="round" />
                <path d="M128,165 L125,160 M272,165 L275,160" stroke="#a1887f" strokeWidth="1" />
                <path d="M190,260 Q200,270 210,260" fill="none" stroke="#d7ccc8" strokeWidth="2" strokeLinecap="round" />
                <path d="M195,200 Q200,260 190,260" fill="none" stroke="#eaddd7" strokeWidth="1.5" />
                <path d="M160,310 Q200,300 240,310 Q200,340 160,310 Z" fill="#eddcd9" />
                <path d="M160,310 Q200,320 240,310" fill="none" stroke="#dcbdb9" strokeWidth="1" />
            </g>
            <g opacity="0.8">
                <FaceZone zone="forehead" d="M100,100 Q200,60 300,100 Q300,120 200,130 Q100,120 100,100 Z" />
                <FaceZone zone="glabella" d="M180,130 L220,130 L210,160 L190,160 Z" />
                <FaceZone zone="crowsFeet" d="M80,150 Q110,150 110,180 Q80,180 80,150 Z M320,150 Q290,150 290,180 Q320,180 320,150 Z" />
                <FaceZone zone="cheeks" d="M120,200 Q160,200 170,230 Q120,250 100,220 Z M280,200 Q240,200 230,230 Q280,250 300,220 Z" />
                <FaceZone zone="nasolabial" d="M180,260 Q160,300 150,320 L165,320 Q175,300 190,260 Z M220,260 Q240,300 250,320 L235,320 Q225,300 210,260 Z" />
                <FaceZone zone="lips" d="M155,305 Q200,295 245,305 Q245,340 200,350 Q155,340 155,305 Z" />
                <FaceZone zone="chin" d="M170,370 Q200,360 230,370 Q230,410 200,430 Q170,410 170,370 Z" />
                <FaceZone zone="jaw" d="M90,300 Q120,400 160,450 L140,470 Q90,420 70,300 Z M310,300 Q280,400 240,450 L260,470 Q310,420 330,300 Z" />
            </g>
            {Object.entries(procedures).map(([key, data]) => {
              const coords: {[key: string]: {x: number, y: number}} = {
                forehead: {x: 200, y: 100}, glabella: {x: 200, y: 145}, crowsFeet: {x: 305, y: 165}, cheeks: {x: 260, y: 220}, nasolabial: {x: 240, y: 290}, lips: {x: 200, y: 325}, chin: {x: 200, y: 395}, jaw: {x: 290, y: 400}
              };
              const pos = coords[key];
              if (!pos) return null;
              return (
                <g key={key} className="pointer-events-none animate-bounce-short">
                  <circle cx={pos.x} cy={pos.y} r="12" fill={data.product === 'toxin' ? '#a855f7' : '#ec4899'} className="shadow-lg" />
                  <text x={pos.x} y={pos.y} dy="4" textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">{data.units}</text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* SIDEBAR DE CONTROLES (Mais compacta) */}
      <aside className="w-full md:w-80 bg-white border-l border-gray-100 p-5 flex flex-col shadow-lg z-20">
        
        {selectedZone ? (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <div>
                <span className="text-[10px] uppercase tracking-wider font-bold text-gray-400">Zona Selecionada</span>
                <h2 className="text-lg font-bold text-gray-800 capitalize">
                  {selectedZone}
                </h2>
              </div>
              <button onClick={() => setSelectedZone(null)} className="text-gray-400 hover:text-gray-600"><Info size={16}/></button>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <button onClick={() => handleAdd(selectedZone, 'toxin')} className="group p-3 rounded-xl border border-purple-100 bg-purple-50 hover:bg-purple-100 transition-colors">
                <Sparkles className="w-5 h-5 text-purple-600 mx-auto mb-1" />
                <span className="block font-bold text-purple-900 text-sm">Botox</span>
                <span className="text-[10px] text-purple-600 font-medium">+2 Unidades</span>
              </button>

              <button onClick={() => handleAdd(selectedZone, 'filler')} className="group p-3 rounded-xl border border-pink-100 bg-pink-50 hover:bg-pink-100 transition-colors">
                <Syringe className="w-5 h-5 text-pink-600 mx-auto mb-1" />
                <span className="block font-bold text-pink-900 text-sm">Preenchedor</span>
                <span className="text-[10px] text-pink-600 font-medium">+1 ML</span>
              </button>
            </div>

            {procedures[selectedZone] && (
               <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 mb-4 flex justify-between items-center">
                  <span className="text-gray-500 text-xs">Total na área: <strong className="text-gray-800">{procedures[selectedZone].units} {procedures[selectedZone].product === 'filler' ? 'ml' : 'u'}</strong></span>
                  <button onClick={() => handleClearZone(selectedZone)} className="text-red-500 hover:text-red-700 transition-colors p-1"><Eraser size={16} /></button>
               </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400 py-10">
             <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mb-2 border border-gray-100">
               <Sparkles size={20} className="text-gray-300"/>
             </div>
             <p className="text-xs">Selecione uma área no rosto.</p>
          </div>
        )}

        <div className="mt-auto pt-4 border-t border-gray-100">
           <div className="flex items-center gap-2 mb-3 text-gray-800 font-bold text-sm">
             <DollarSign className="text-green-500 w-4 h-4"/> Orçamento
           </div>
           
           <div className="space-y-1 mb-4 max-h-32 overflow-y-auto custom-scrollbar">
             {Object.entries(procedures).map(([key, data]) => (
               <div key={key} className="flex justify-between text-xs items-center py-1 border-b border-gray-50">
                 <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${data.product === 'toxin' ? 'bg-purple-500' : 'bg-pink-500'}`}></div>
                    <span className="capitalize text-gray-600">{key}</span>
                 </div>
                 <div className="text-right flex items-center gap-2">
                    <span className="text-[10px] text-gray-400">{data.units}{data.product === 'filler' ? 'ml' : 'u'}</span>
                    <span className="font-bold text-gray-700">R$ {data.price}</span>
                 </div>
               </div>
             ))}
           </div>

           <div className="flex justify-between items-end mb-3">
              <span className="text-gray-400 text-xs">Total</span>
              <span className="text-2xl font-bold text-gray-800 tracking-tight leading-none">R$ {calculateTotal()}</span>
           </div>

           <button className="w-full bg-gray-900 hover:bg-black text-white font-bold py-3 rounded-lg text-sm transition-all shadow-lg flex items-center justify-center gap-2">
             <Save size={16} /> Salvar
           </button>
        </div>
      </aside>
    </div>
  );
}