import React, { useState, useEffect } from 'react';
import { 
  Calendar as CalIcon, ChevronLeft, ChevronRight, Plus, 
  Check, Clock, AlertCircle, Loader2, Search 
} from 'lucide-react';

type Status = 'confirmed' | 'pending' | 'canceled' | 'completed';

interface Appointment {
  id: string; 
  patient: string; 
  procedure: string; 
  day: number; 
  hour: number; 
  duration: number; 
  status: Status;
}

export function Agenda() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  // Simulação de carregamento do banco que acabamos de popular
  useEffect(() => {
    const fetchAgenda = async () => {
      try {
        const token = localStorage.getItem('odonto_token');
        // No futuro, esta rota buscará os dados do seu seed_db.py
        const res = await fetch('/api/appointments', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        // Fallback para os dados do Seed caso a rota ainda não esteja pronta
        if (Array.isArray(data) && data.length > 0) {
          setAppointments(data);
        } else {
          setAppointments([
            { id: '1', patient: 'Carlos Eduardo', procedure: 'Avaliação Geral', day: 1, hour: 9, duration: 1, status: 'confirmed' },
            { id: '2', patient: 'Mariana Souza', procedure: 'Clareamento', day: 1, hour: 14, duration: 2, status: 'confirmed' },
            { id: '3', patient: 'Roberto Lima', procedure: 'Extração', day: 2, hour: 10, duration: 1, status: 'pending' },
          ]);
        }
      } catch (error) {
        console.error("Erro ao carregar agenda", error);
      } finally {
        setLoading(false);
      }
    };
    fetchAgenda();
  }, []);

  const hours = Array.from({ length: 11 }, (_, i) => i + 8);
  const weekDays = [
    { day: 1, label: 'Seg', date: '26' }, { day: 2, label: 'Ter', date: '27' },
    { day: 3, label: 'Qua', date: '28' }, { day: 4, label: 'Qui', date: '29' },
    { day: 5, label: 'Sex', date: '30' },
  ];

  const getStatusColor = (status: Status) => {
    switch(status) {
      case 'confirmed': return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'pending': return 'bg-orange-50 border-orange-200 text-orange-700';
      case 'canceled': return 'bg-red-50 border-red-200 text-red-700 opacity-60';
      default: return 'bg-gray-50 border-gray-200 text-gray-500';
    }
  };

  if (loading) return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <Loader2 className="animate-spin text-blue-600" size={48} />
    </div>
  );

  return (
    <div className="flex flex-col h-screen bg-gray-50 p-8 font-sans overflow-hidden">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-2xl shadow-lg shadow-blue-200">
              <CalIcon className="text-white w-6 h-6"/>
            </div> 
            Agenda Clínica
          </h1>
          <p className="text-gray-500 font-medium mt-1">Gestão inteligente de horários e salas.</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center bg-white p-1 rounded-2xl shadow-sm border border-gray-100">
            <button className="p-2 hover:bg-gray-50 text-gray-400 rounded-xl transition-all"><ChevronLeft size={20} /></button>
            <span className="font-black text-gray-700 px-4 text-xs uppercase tracking-widest">Janeiro, 2026</span>
            <button className="p-2 hover:bg-gray-50 text-gray-400 rounded-xl transition-all"><ChevronRight size={20} /></button>
          </div>
          <button className="bg-blue-600 text-white px-6 py-3 rounded-2xl flex items-center gap-2 hover:bg-blue-700 shadow-xl shadow-blue-100 text-xs font-black uppercase tracking-widest transition-all active:scale-95">
            <Plus size={18} /> Novo Horário
          </button>
        </div>
      </header>

      <div className="flex-1 bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden flex flex-col relative">
        {/* Header da Grade */}
        <div className="grid grid-cols-6 bg-gray-50/50 border-b border-gray-100">
          <div className="p-4 border-r border-gray-100 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">Hora</div>
          {weekDays.map(d => (
            <div key={d.day} className="p-4 text-center border-r border-gray-100 last:border-0">
              <span className="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">{d.label}</span>
              <div className={`w-8 h-8 mx-auto flex items-center justify-center rounded-2xl font-black text-sm transition-all ${d.date === '28' ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' : 'text-gray-800 hover:bg-gray-200'}`}>
                {d.date}
              </div>
            </div>
          ))}
        </div>

        {/* Corpo da Grade */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="grid grid-cols-6 relative">
            <div className="border-r border-gray-100 bg-gray-50/20">
              {hours.map(hour => (
                <div key={hour} className="h-24 border-b border-gray-50 text-[10px] text-gray-400 font-black flex justify-center pt-4 tracking-tighter">
                  {hour}:00
                </div>
              ))}
            </div>

            {weekDays.map(dayInfo => (
              <div key={dayInfo.day} className="border-r border-gray-100 last:border-0 relative bg-white">
                {hours.map(hour => {
                  const appt = appointments.find(a => a.day === dayInfo.day && a.hour === hour);
                  return (
                    <div key={`${dayInfo.day}-${hour}`} className="h-24 border-b border-gray-50 border-dashed relative group hover:bg-blue-50/20 transition-colors">
                      {!appt && (
                        <button className="absolute inset-0 w-full h-full opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                          <Plus size={20} className="text-blue-300"/>
                        </button>
                      )}
                      {appt && (
                        <div 
                          className={`absolute inset-x-2 inset-y-2 rounded-[1.5rem] p-4 border-l-4 shadow-sm cursor-pointer z-10 transition-all hover:shadow-md hover:scale-[1.02] ${getStatusColor(appt.status)}`}
                          style={{ height: `${appt.duration * 96 - 16}px` }} 
                        >
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-[9px] font-black uppercase tracking-widest flex items-center gap-1 opacity-70">
                               {appt.status === 'confirmed' ? <Check size={10} /> : <Clock size={10} />}
                               {appt.hour}:00
                            </span>
                          </div>
                          <p className="font-black text-xs text-gray-800 leading-tight mb-1">{appt.patient}</p>
                          <p className="text-[10px] font-bold opacity-60 uppercase tracking-tighter">{appt.procedure}</p>
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