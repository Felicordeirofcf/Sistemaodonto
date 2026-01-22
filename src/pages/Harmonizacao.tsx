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

  const PRICES = { 
    toxin: 45,    
    filler: 900,  
    threads: 250  
  };

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

  const calculateTotal = () => {
    return Object.values(procedures).reduce((acc, curr) => acc + curr.price, 0);
  };

  // --- CORREÇÃO AQUI: Removi 'label' que não estava sendo usado ---
  const FaceZone = ({ zone, d }: { zone: Zone, d: string }) => {
    const data = procedures[zone];
    const isSelected = selectedZone === zone;
    const hasProduct = !!data;
    
    const fillColor = data?.product === 'toxin' ? 'fill-purple-200' : 'fill-pink-200';
    const strokeColor = data?.product === 'toxin' ? 'stroke-purple-500' : 'stroke-pink-500';

    return (
      <g 
        onClick={() => setSelectedZone(zone)} 
        className="cursor-pointer group transition-all duration-300"
      >
        <path 
          d={d} 
          className={`transition-all duration-500 ease-in-out
            ${hasProduct ? `${fillColor} ${strokeColor} opacity-90` : 'fill-transparent stroke-transparent hover:fill-blue-50/50 hover:stroke-blue-200'}
            ${isSelected ? 'stroke-[2px] filter drop-shadow-md' : 'stroke-[1px]'}
          `}
        />
        {hasProduct && (
          <foreignObject x="0" y="0" width="100%" height="100%" className="pointer-events-none overflow-visible">
          </foreignObject>
        )}
      </g>
    );
  };

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-50 overflow-hidden font-sans">
      
      <div className="flex-1 p-2 md:p-6 overflow-y-auto flex flex-col items-center relative custom-scrollbar">
        
        <div className="absolute top-6 left-6 z-10 bg-white/80 backdrop-blur px-4 py-2 rounded-full border border-gray-100 shadow-sm">
          <h1 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <Sparkles className="text-purple-500 w-5 h-5" /> 
            Face Mapping 3D
          </h1>
        </div>

        <div className="relative w-full max-w-[450px] aspect-[3/4.2] my-auto">
          
          <svg viewBox="0 0 400 550" className="w-full h-full drop-shadow-2xl">
            <defs>
              <linearGradient id="skinGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#fffcf9" />
                <stop offset="100%" stopColor="#fcefe9" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>

            <g className="pointer-events-none">
                <path d="M70,150 C70,50 330,50 330,150 C330,280 300,400 200,480 C100,400 70,280 70,150 Z" 
                      fill="url(#skinGradient)" stroke="#e2d5ce" strokeWidth="2" />
                
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
                forehead: {x: 200, y: 100},
                glabella: {x: 200, y: 145},
                crowsFeet: {x: 305, y: 165},
                cheeks: {x: 260, y: 220},
                nasolabial: {x: 240, y: 290},
                lips: {x: 200, y: 325},
                chin: {x: 200, y: 395},
                jaw: {x: 290, y: 400}
              };
              const pos = coords[key];
              if (!pos) return null;

              return (
                <g key={key} className="pointer-events-none animate-bounce-short">
                  <circle cx={pos.x} cy={pos.y} r="14" fill={data.product === 'toxin' ? '#a855f7' : '#ec4899'} className="shadow-lg" />
                  <text x={pos.x} y={pos.y} dy="5" textAnchor="middle" fill="white" fontSize="11" fontWeight="bold">
                    {data.units}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className="absolute bottom-4 right-4 flex flex-col gap-2 text-[10px] font-medium text-gray-400 bg-white/50 p-2 rounded-lg backdrop-blur-sm">
             <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-purple-500"></div> Botox</div>
             <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-pink-500"></div> Preenchedor</div>
          </div>
        </div>
      </div>

      <aside className="w-full md:w-96 bg-white border-l border-gray-100 p-6 flex flex-col shadow-[0_0_40px_rgba(0,0,0,0.05)] z-20">
        
        {selectedZone ? (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <div>
                <span className="text-xs uppercase tracking-wider font-bold text-gray-400">Zona Selecionada</span>
                <h2 className="text-2xl font-bold text-gray-800 capitalize">
                  {selectedZone === 'crowsFeet' ? 'Olhos / Pés de Galinha' : 
                   selectedZone === 'nasolabial' ? 'Bigode Chinês' :
                   selectedZone === 'glabella' ? 'Glabela' :
                   selectedZone === 'jaw' ? 'Mandíbula' : 
                   selectedZone === 'cheeks' ? 'Malar' : 
                   selectedZone === 'forehead' ? 'Testa' : 
                   selectedZone === 'chin' ? 'Queixo' : 'Lábios'}
                </h2>
              </div>
              <button onClick={() => setSelectedZone(null)} className="text-gray-400 hover:text-gray-600">
                <Info size={20}/>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <button 
                onClick={() => handleAdd(selectedZone, 'toxin')}
                className="group relative overflow-hidden p-4 rounded-2xl border border-purple-100 bg-purple-50/50 hover:bg-purple-100 transition-all text-center"
              >
                <div className="absolute inset-0 bg-purple-200/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                <Sparkles className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                <span className="block font-bold text-purple-900">Botox</span>
                <span className="text-xs text-purple-600 font-medium">+2 Unidades</span>
              </button>

              <button 
                onClick={() => handleAdd(selectedZone, 'filler')}
                className="group relative overflow-hidden p-4 rounded-2xl border border-pink-100 bg-pink-50/50 hover:bg-pink-100 transition-all text-center"
              >
                <div className="absolute inset-0 bg-pink-200/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                <Syringe className="w-8 h-8 text-pink-600 mx-auto mb-2" />
                <span className="block font-bold text-pink-900">Preenchimento</span>
                <span className="text-xs text-pink-600 font-medium">+1 ML</span>
              </button>
            </div>

            {procedures[selectedZone] && (
               <div className="bg-gray-50 p-4 rounded-xl border border-gray-100 mb-4 animate-scale-in">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-gray-500 text-sm font-medium">Aplicado nesta região:</span>
                    <span className="font-bold text-xl text-gray-800">
                        {procedures[selectedZone].units} {procedures[selectedZone].product === 'filler' ? 'ml' : 'u'}
                    </span>
                  </div>
                  <button 
                    onClick={() => handleClearZone(selectedZone)}
                    className="w-full py-2.5 text-red-500 text-sm font-medium hover:bg-red-50 rounded-lg flex items-center justify-center gap-2 transition-colors border border-transparent hover:border-red-100"
                  >
                    <Eraser size={16} /> Remover Aplicação
                  </button>
               </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400">
             <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-4 border border-gray-100">
               <Sparkles size={32} className="text-gray-300"/>
             </div>
             <h3 className="text-gray-600 font-bold mb-1">Toque no Rosto</h3>
             <p className="text-sm max-w-[200px]">Selecione uma área no mapa para começar o planejamento.</p>
          </div>
        )}

        <div className="mt-auto pt-6 border-t border-gray-100">
           <div className="flex items-center gap-2 mb-4 text-gray-800 font-bold">
             <DollarSign className="text-green-500 w-5 h-5"/> Resumo do Plano
           </div>
           
           <div className="space-y-2 mb-6 max-h-32 overflow-y-auto custom-scrollbar pr-2">
             {Object.entries(procedures).map(([key, data]) => (
               <div key={key} className="flex justify-between text-sm items-center group">
                 <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${data.product === 'toxin' ? 'bg-purple-500' : 'bg-pink-500'}`}></div>
                    <span className="capitalize text-gray-600 font-medium">
                        {key === 'crowsFeet' ? 'Olhos' : key === 'nasolabial' ? 'Bigode C.' : key}
                    </span>
                 </div>
                 <div className="text-right flex items-center gap-3">
                    <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded">{data.units}{data.product === 'filler' ? 'ml' : 'u'}</span>
                    <span className="font-bold text-gray-700">R$ {data.price}</span>
                 </div>
               </div>
             ))}
             {Object.keys(procedures).length === 0 && (
                <p className="text-center text-gray-400 text-sm py-4 italic bg-gray-50/50 rounded-lg border border-dashed border-gray-200">
                    Nenhum procedimento selecionado.
                </p>
             )}
           </div>

           <div className="flex justify-between items-end mb-4">
              <span className="text-gray-400 text-sm font-medium">Investimento Total</span>
              <span className="text-3xl font-bold text-gray-800 tracking-tight">
                  R$ {calculateTotal()}
                  <span className="text-sm font-normal text-gray-400 ml-1">,00</span>
              </span>
           </div>

           <button className="w-full bg-gray-900 hover:bg-black text-white font-bold py-4 rounded-xl transition-all shadow-xl hover:shadow-2xl flex items-center justify-center gap-2 active:scale-95">
             <Save size={20} /> Finalizar Orçamento
           </button>
        </div>
      </aside>
    </div>
  );
}