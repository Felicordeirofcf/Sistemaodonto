import { useState } from 'react';
import { Calendar as CalIcon, ChevronLeft, ChevronRight, Plus, Check, Clock, AlertCircle } from 'lucide-react';

type Status = 'confirmed' | 'pending' | 'canceled' | 'completed';

interface Appointment {
  id: string; patient: string; procedure: string; day: number; hour: number; duration: number; status: Status;
}

export function Agenda() {
  const [appointments] = useState<Appointment[]>([
    { id: '1', patient: 'Ana Julia', procedure: 'Clareamento', day: 1, hour: 9, duration: 1, status: 'confirmed' },
    { id: '2', patient: 'Carlos D.', procedure: 'Extração', day: 1, hour: 14, duration: 2, status: 'confirmed' },
    { id: '3', patient: 'Marcos P.', procedure: 'Avaliação', day: 2, hour: 10, duration: 1, status: 'pending' },
  ]);

  const hours = Array.from({ length: 11 }, (_, i) => i + 8);
  const weekDays = [
    { day: 1, label: 'Seg', date: '22' }, { day: 2, label: 'Ter', date: '23' },
    { day: 3, label: 'Qua', date: '24' }, { day: 4, label: 'Qui', date: '25' },
    { day: 5, label: 'Sex', date: '26' },
  ];

  const getStatusColor = (status: Status) => {
    switch(status) {
      case 'confirmed': return 'bg-green-100 border-green-200 text-green-700';
      case 'pending': return 'bg-yellow-100 border-yellow-200 text-yellow-700';
      case 'canceled': return 'bg-red-100 border-red-200 text-red-700 line-through opacity-60';
      default: return 'bg-gray-100 border-gray-200 text-gray-500';
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 p-4 font-sans text-sm overflow-hidden">
      <header className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <CalIcon className="text-primary w-5 h-5"/> Agenda
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-white border border-gray-200 rounded-md shadow-sm">
            <button className="p-1 hover:bg-gray-50 text-gray-600"><ChevronLeft size={16} /></button>
            <span className="font-bold text-gray-700 px-3 text-xs">Junho, 2026</span>
            <button className="p-1 hover:bg-gray-50 text-gray-600"><ChevronRight size={16} /></button>
          </div>
          <button className="bg-primary text-white px-3 py-1.5 rounded-md flex items-center gap-1 hover:bg-blue-700 shadow-sm text-xs font-bold">
            <Plus size={14} /> Novo
          </button>
        </div>
      </header>

      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
        <div className="grid grid-cols-6 border-b border-gray-200 bg-gray-50/50">
          <div className="p-2 border-r border-gray-200 text-center text-[10px] font-bold text-gray-400 uppercase">H</div>
          {weekDays.map(d => (
            <div key={d.day} className="p-2 text-center border-r border-gray-100 last:border-0">
              <span className="text-[10px] text-gray-500 uppercase font-bold">{d.label}</span>
              <div className={`mt-0.5 w-6 h-6 mx-auto flex items-center justify-center rounded-full font-bold text-xs ${d.day === 1 ? 'bg-primary text-white' : 'text-gray-700'}`}>
                {d.date}
              </div>
            </div>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="grid grid-cols-6 relative">
            <div className="border-r border-gray-200 bg-white">
              {hours.map(hour => (
                <div key={hour} className="h-16 border-b border-gray-50 text-[10px] text-gray-400 font-medium flex justify-center pt-1">
                  {hour}:00
                </div>
              ))}
            </div>

            {weekDays.map(dayInfo => (
              <div key={dayInfo.day} className="border-r border-gray-50 last:border-0 relative bg-white">
                {hours.map(hour => {
                  const appt = appointments.find(a => a.day === dayInfo.day && a.hour === hour);
                  return (
                    <div key={`${dayInfo.day}-${hour}`} className="h-16 border-b border-gray-50 border-dashed relative group hover:bg-gray-50/50">
                      {!appt && (
                        <button className="absolute inset-0 w-full h-full opacity-0 group-hover:opacity-100 flex items-center justify-center">
                          <Plus size={14} className="text-blue-400"/>
                        </button>
                      )}
                      {appt && (
                        <div 
                          className={`absolute inset-x-0.5 inset-y-0.5 rounded p-1.5 border-l-2 shadow-sm cursor-pointer z-10 ${getStatusColor(appt.status)}`}
                          style={{ height: `${appt.duration * 64 - 4}px` }} 
                        >
                          <div className="flex justify-between items-start leading-none mb-1">
                            <span className="text-[10px] font-bold truncate flex items-center gap-1">
                               {appt.status === 'confirmed' ? <Check size={8} /> : appt.status === 'pending' ? <Clock size={8} /> : <AlertCircle size={8} />}
                               {appt.hour}:00
                            </span>
                          </div>
                          <p className="font-bold text-[11px] truncate leading-tight">{appt.patient}</p>
                          <p className="text-[9px] opacity-80 truncate">{appt.procedure}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}