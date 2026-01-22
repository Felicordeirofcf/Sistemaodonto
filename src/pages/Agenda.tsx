import { useState } from 'react';
import { Calendar as CalIcon, ChevronLeft, ChevronRight, Clock, Plus, Check, AlertCircle } from 'lucide-react';

// Tipos
type Status = 'confirmed' | 'pending' | 'canceled' | 'completed';

interface Appointment {
  id: string;
  patient: string;
  procedure: string;
  day: number; // 0 = Domingo, 1 = Segunda...
  hour: number; // 9, 10, 11...
  duration: number; // 1 (1 hora)
  status: Status;
}

export function Agenda() {
  // Removi o currentDate pois era estático na visualização
  
  // Simulação de Dados (Banco de Dados Fake) - Removi o setAppointments pois não estamos alterando dados ainda
  const [appointments] = useState<Appointment[]>([
    { id: '1', patient: 'Ana Julia', procedure: 'Clareamento', day: 1, hour: 9, duration: 1, status: 'confirmed' },
    { id: '2', patient: 'Carlos D.', procedure: 'Extração Sis', day: 1, hour: 14, duration: 2, status: 'confirmed' },
    { id: '3', patient: 'Marcos P.', procedure: 'Avaliação', day: 2, hour: 10, duration: 1, status: 'pending' },
    { id: '4', patient: 'Luana S.', procedure: 'Manutenção', day: 3, hour: 11, duration: 1, status: 'completed' },
    { id: '5', patient: 'Pedro H.', procedure: 'Implante', day: 4, hour: 15, duration: 2, status: 'canceled' },
  ]);

  // Horários de atendimento (08:00 as 18:00)
  const hours = Array.from({ length: 11 }, (_, i) => i + 8);
  
  // Dias da semana úteis (Segunda a Sexta)
  const weekDays = [
    { day: 1, label: 'Segunda', date: '22' },
    { day: 2, label: 'Terça', date: '23' },
    { day: 3, label: 'Quarta', date: '24' },
    { day: 4, label: 'Quinta', date: '25' },
    { day: 5, label: 'Sexta', date: '26' },
  ];

  // Funções Auxiliares
  const getStatusColor = (status: Status) => {
    switch(status) {
      case 'confirmed': return 'bg-green-100 border-green-200 text-green-700';
      case 'pending': return 'bg-yellow-100 border-yellow-200 text-yellow-700';
      case 'canceled': return 'bg-red-100 border-red-200 text-red-700 line-through opacity-60';
      case 'completed': return 'bg-gray-100 border-gray-200 text-gray-500';
      default: return 'bg-blue-100 text-blue-700';
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 p-4 md:p-6 overflow-hidden">
      
      {/* CABEÇALHO */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800 flex items-center gap-2">
            <CalIcon className="text-primary"/> Agenda Clínica
          </h1>
          <p className="text-gray-500 text-sm">Gerencie os horários do Dr. Fonseca</p>
        </div>

        <div className="flex items-center gap-3 bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
          <button className="p-2 hover:bg-gray-100 rounded-md text-gray-600">
            <ChevronLeft size={20} />
          </button>
          <span className="font-bold text-gray-700 px-2 min-w-[140px] text-center">
            Junho, 2026
          </span>
          <button className="p-2 hover:bg-gray-100 rounded-md text-gray-600">
            <ChevronRight size={20} />
          </button>
        </div>

        <button className="bg-primary text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 shadow-md transition-transform active:scale-95">
          <Plus size={18} /> Novo Agendamento
        </button>
      </header>

      {/* GRID DO CALENDÁRIO */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
        
        {/* Cabeçalho dos Dias */}
        <div className="grid grid-cols-6 border-b border-gray-200 bg-gray-50">
          <div className="p-4 border-r border-gray-200 text-center text-xs font-bold text-gray-400 uppercase">
            Horário
          </div>
          {weekDays.map(d => (
            <div key={d.day} className="p-3 text-center border-r border-gray-100 last:border-0">
              <span className="text-xs text-gray-500 uppercase font-semibold">{d.label}</span>
              <div className={`mt-1 w-8 h-8 mx-auto flex items-center justify-center rounded-full font-bold text-sm ${d.day === 1 ? 'bg-primary text-white shadow-blue-200 shadow-md' : 'text-gray-700'}`}>
                {d.date}
              </div>
            </div>
          ))}
        </div>

        {/* Corpo da Agenda (Scrollável) */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-6">
            
            {/* Coluna de Horas */}
            <div className="border-r border-gray-200 bg-white">
              {hours.map(hour => (
                <div key={hour} className="h-24 border-b border-gray-100 text-xs text-gray-400 font-medium flex justify-center pt-2">
                  {hour}:00
                </div>
              ))}
            </div>

            {/* Colunas dos Dias */}
            {weekDays.map(dayInfo => (
              <div key={dayInfo.day} className="border-r border-gray-100 last:border-0 relative bg-white">
                {hours.map(hour => {
                  const appt = appointments.find(a => a.day === dayInfo.day && a.hour === hour);
                  
                  return (
                    <div key={`${dayInfo.day}-${hour}`} className="h-24 border-b border-gray-50 border-dashed relative group hover:bg-gray-50 transition-colors">
                      {!appt && (
                        <button className="absolute inset-0 w-full h-full opacity-0 group-hover:opacity-100 flex items-center justify-center">
                          <div className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-bold shadow-sm border border-blue-100">
                             + Agendar
                          </div>
                        </button>
                      )}

                      {appt && (
                        <div 
                          className={`absolute inset-x-1 inset-y-1 rounded-lg p-2 border-l-4 shadow-sm cursor-pointer hover:shadow-md transition-all z-10 ${getStatusColor(appt.status)}`}
                          style={{ height: `${appt.duration * 96 - 8}px` }} 
                        >
                          <div className="flex justify-between items-start">
                            <span className="text-xs font-bold truncate flex items-center gap-1">
                               {appt.status === 'confirmed' && <Check size={10} />}
                               {appt.status === 'pending' && <Clock size={10} />}
                               {appt.status === 'canceled' && <AlertCircle size={10} />}
                               {appt.hour}:00
                            </span>
                          </div>
                          <div className="mt-1">
                            <p className="font-bold text-sm truncate">{appt.patient}</p>
                            <p className="text-xs opacity-80 truncate">{appt.procedure}</p>
                          </div>
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
      
      {/* LEGENDA (Rodapé) */}
      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
         <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-green-500"></div> Confirmado</div>
         <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-yellow-500"></div> Pendente</div>
         <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-blue-500"></div> Em Aberto</div>
         <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-400"></div> Cancelado</div>
      </div>

    </div>
  );
}