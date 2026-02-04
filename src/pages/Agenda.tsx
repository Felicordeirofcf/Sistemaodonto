import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar as CalIcon, ChevronLeft, ChevronRight, Plus,
  Check, Clock, Loader2, X, Trash2
} from 'lucide-react';

type Status = 'scheduled' | 'confirmed' | 'done' | 'cancelled';

interface Appointment {
  id: number;
  title: string;
  description: string;

  // ✅ backend pode mandar start/end OU start_datetime/end_datetime OU date_time
  start?: string;
  end?: string;
  start_datetime?: string;
  end_datetime?: string;
  date_time?: string;

  status: Status;
  patient_id?: number;
  lead_id?: number;
}

type NormalizedAppointment = {
  id: number;
  title: string;
  description: string;
  startLocal: Date;
  endLocal: Date;
  status: Status;
  patient_id?: number;
  lead_id?: number;
};

// ✅ parse robusto para strings "YYYY-MM-DD HH:MM" (sem timezone) ou ISO
function parseDateTimeLoose(value?: string): Date | null {
  if (!value) return null;

  // ISO
  if (value.includes('T')) {
    const d = new Date(value);
    return isNaN(d.getTime()) ? null : d;
  }

  // "YYYY-MM-DD HH:MM:SS" ou "YYYY-MM-DD HH:MM"
  const m = value.match(/^(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?$/);
  if (m) {
    const y = Number(m[1]);
    const mo = Number(m[2]) - 1;
    const da = Number(m[3]);
    const hh = Number(m[4] ?? 9);
    const mm = Number(m[5] ?? 0);
    const ss = Number(m[6] ?? 0);
    // ✅ cria como LOCAL (evita virar dia anterior por UTC)
    const d = new Date(y, mo, da, hh, mm, ss, 0);
    return isNaN(d.getTime()) ? null : d;
  }

  // fallback
  const d = new Date(value);
  return isNaN(d.getTime()) ? null : d;
}

function toYMDLocal(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function toHMLocal(date: Date): string {
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

function normalizeAppointment(a: Appointment): NormalizedAppointment | null {
  const startStr = a.start_datetime || a.start || a.date_time;
  const endStr = a.end_datetime || a.end;

  const startLocal = parseDateTimeLoose(startStr);
  if (!startLocal) return null;

  const endLocal = parseDateTimeLoose(endStr) || new Date(startLocal.getTime() + 30 * 60 * 1000);

  return {
    id: a.id,
    title: a.title || 'Consulta',
    description: a.description || '',
    startLocal,
    endLocal,
    status: a.status || 'scheduled',
    patient_id: a.patient_id,
    lead_id: a.lead_id,
  };
}

export function Agenda() {
  const [appointments, setAppointments] = useState<NormalizedAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedAppt, setSelectedAppt] = useState<NormalizedAppointment | null>(null);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    date: toYMDLocal(new Date()),
    time: '09:00',
    duration: '30', // ✅ minutos (mais realista que "1")
    status: 'scheduled' as Status
  });

  const fetchAgenda = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('odonto_token');
      const res = await fetch('/api/appointments', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await res.json();

      if (Array.isArray(data)) {
        const normalized = data
          .map((a: Appointment) => normalizeAppointment(a))
          .filter(Boolean) as NormalizedAppointment[];

        setAppointments(normalized);
      } else {
        setAppointments([]);
      }
    } catch (error) {
      console.error("Erro ao carregar agenda", error);
      setAppointments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAgenda(); }, [fetchAgenda]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const token = localStorage.getItem('odonto_token');

      // ✅ manda em formato compatível (backend pode aceitar start + duration)
      const start = `${formData.date} ${formData.time}`; // "YYYY-MM-DD HH:MM" (local)
      const payload = {
        title: formData.title,
        description: formData.description,
        start,                // ✅ local string
        duration: formData.duration, // ✅ minutos
        status: formData.status
      };

      const url = selectedAppt ? `/api/appointments/${selectedAppt.id}` : '/api/appointments';
      const method = selectedAppt ? 'PATCH' : 'POST';

      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setIsModalOpen(false);
        setSelectedAppt(null);
        await fetchAgenda();
      } else {
        console.error("Erro ao salvar. Status:", res.status);
      }
    } catch (error) {
      console.error("Erro ao salvar:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Excluir este agendamento?")) return;
    try {
      const token = localStorage.getItem('odonto_token');
      const res = await fetch(`/api/appointments/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        await fetchAgenda();
        setIsModalOpen(false);
        setSelectedAppt(null);
      } else {
        console.error("Erro ao excluir. Status:", res.status);
      }
    } catch (error) {
      console.error("Erro ao excluir:", error);
    }
  };

  const openCreateModal = (date?: string, time?: string) => {
    setSelectedAppt(null);
    setFormData({
      title: '',
      description: '',
      date: date || toYMDLocal(new Date()),
      time: time || '09:00',
      duration: '30',
      status: 'scheduled'
    });
    setIsModalOpen(true);
  };

  const openEditModal = (appt: NormalizedAppointment) => {
    setSelectedAppt(appt);
    setFormData({
      title: appt.title,
      description: appt.description,
      date: toYMDLocal(appt.startLocal),
      time: toHMLocal(appt.startLocal),
      duration: '30',
      status: appt.status
    });
    setIsModalOpen(true);
  };

  // Calendar Helpers
  const hours = Array.from({ length: 11 }, (_, i) => i + 8);

  const getStartOfWeek = (date: Date) => {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    d.setHours(0, 0, 0, 0);
    return new Date(d.setDate(diff));
  };

  const startOfWeek = getStartOfWeek(currentDate);

  // ✅ fullDate local (evita bugs de UTC)
  const weekDays = Array.from({ length: 5 }, (_, i) => {
    const d = new Date(startOfWeek);
    d.setDate(d.getDate() + i);
    return {
      day: i + 1,
      label: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex'][i],
      date: d.getDate().toString(),
      fullDate: toYMDLocal(d)
    };
  });

  const todayYMD = toYMDLocal(new Date());

  const getStatusColor = (status: Status) => {
    switch (status) {
      case 'confirmed': return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'scheduled': return 'bg-orange-50 border-orange-200 text-orange-700';
      case 'cancelled': return 'bg-red-50 border-red-200 text-red-700 opacity-60';
      case 'done': return 'bg-green-50 border-green-200 text-green-700';
      default: return 'bg-gray-50 border-gray-200 text-gray-500';
    }
  };

  if (loading) return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <Loader2 className="animate-spin text-blue-600" size={48} />
    </div>
  );

  return (
    <div className="flex flex-col h-screen bg-gray-50 p-8 font-sans overflow-hidden relative">

      {isModalOpen && (
        <div className="fixed inset-0 z-[100] bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white p-8 rounded-[2.5rem] w-full max-w-md shadow-2xl animate-in zoom-in duration-200">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-black text-gray-800">
                {selectedAppt ? 'Editar Agendamento' : 'Novo Agendamento'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Título / Paciente</label>
                <input
                  required
                  placeholder="Ex: João Silva - Avaliação"
                  className="w-full p-3 bg-gray-50 border border-gray-100 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                  value={formData.title}
                  onChange={e => setFormData({ ...formData, title: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Data</label>
                  <input
                    type="date"
                    required
                    className="w-full p-3 bg-gray-50 border rounded-xl outline-none"
                    value={formData.date}
                    onChange={e => setFormData({ ...formData, date: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Horário</label>
                  <input
                    type="time"
                    required
                    className="w-full p-3 bg-gray-50 border rounded-xl outline-none"
                    value={formData.time}
                    onChange={e => setFormData({ ...formData, time: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Procedimento / Notas</label>
                <textarea
                  className="w-full p-3 bg-gray-50 border rounded-xl outline-none"
                  rows={2}
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-black uppercase text-gray-400 ml-1">Status</label>
                <select
                  className="w-full p-3 bg-gray-50 border rounded-xl outline-none"
                  value={formData.status}
                  onChange={e => setFormData({ ...formData, status: e.target.value as Status })}
                >
                  <option value="scheduled">Agendado</option>
                  <option value="confirmed">Confirmado</option>
                  <option value="done">Concluído</option>
                  <option value="cancelled">Cancelado</option>
                </select>
              </div>

              <div className="flex gap-3 mt-4">
                {selectedAppt && (
                  <button
                    type="button"
                    onClick={() => handleDelete(selectedAppt.id)}
                    className="p-4 bg-red-50 text-red-600 rounded-2xl hover:bg-red-100 transition-colors"
                  >
                    <Trash2 size={20} />
                  </button>
                )}
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-blue-600 text-white py-4 rounded-2xl font-black uppercase tracking-widest shadow-xl shadow-blue-100 flex items-center justify-center gap-2"
                >
                  {saving ? <Loader2 className="animate-spin" /> : 'Salvar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-2xl shadow-lg shadow-blue-200">
              <CalIcon className="text-white w-6 h-6" />
            </div>
            Agenda Clínica
          </h1>
          <p className="text-gray-500 font-medium mt-1">Gestão inteligente de horários e salas.</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center bg-white p-1 rounded-2xl shadow-sm border border-gray-100">
            <button
              onClick={() => {
                const d = new Date(currentDate);
                d.setDate(d.getDate() - 7);
                setCurrentDate(d);
              }}
              className="p-2 hover:bg-gray-50 text-gray-400 rounded-xl transition-all"
            >
              <ChevronLeft size={20} />
            </button>
            <span className="font-black text-gray-700 px-4 text-xs uppercase tracking-widest">
              {currentDate.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}
            </span>
            <button
              onClick={() => {
                const d = new Date(currentDate);
                d.setDate(d.getDate() + 7);
                setCurrentDate(d);
              }}
              className="p-2 hover:bg-gray-50 text-gray-400 rounded-xl transition-all"
            >
              <ChevronRight size={20} />
            </button>
          </div>
          <button
            onClick={() => openCreateModal()}
            className="bg-blue-600 text-white px-6 py-3 rounded-2xl flex items-center gap-2 hover:bg-blue-700 shadow-xl shadow-blue-100 text-xs font-black uppercase tracking-widest transition-all active:scale-95"
          >
            <Plus size={18} /> Novo Horário
          </button>
        </div>
      </header>

      <div className="flex-1 bg-white rounded-[2.5rem] shadow-sm border border-gray-100 overflow-hidden flex flex-col relative">
        <div className="grid grid-cols-6 bg-gray-50/50 border-b border-gray-100">
          <div className="p-4 border-r border-gray-100 text-center text-[10px] font-black text-gray-400 uppercase tracking-widest">Hora</div>
          {weekDays.map(d => (
            <div key={d.day} className="p-4 text-center border-r border-gray-100 last:border-0">
              <span className="text-[10px] text-gray-400 uppercase font-black tracking-widest block mb-1">{d.label}</span>
              <div className={`w-8 h-8 mx-auto flex items-center justify-center rounded-2xl font-black text-sm transition-all ${d.fullDate === todayYMD ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' : 'text-gray-800 hover:bg-gray-200'}`}>
                {d.date}
              </div>
            </div>
          ))}
        </div>

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
                  const hourStr = hour.toString().padStart(2, '0');

                  // ✅ busca appointment por data local + hora local (sem toISOString)
                  const appt = appointments.find(a => (
                    toYMDLocal(a.startLocal) === dayInfo.fullDate &&
                    a.startLocal.getHours() === hour
                  ));

                  return (
                    <div key={`${dayInfo.day}-${hour}`} className="h-24 border-b border-gray-50 border-dashed relative group hover:bg-blue-50/20 transition-colors">
                      {!appt && (
                        <button
                          onClick={() => openCreateModal(dayInfo.fullDate, `${hourStr}:00`)}
                          className="absolute inset-0 w-full h-full opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"
                        >
                          <Plus size={20} className="text-blue-300" />
                        </button>
                      )}
                      {appt && (
                        <div
                          onClick={() => openEditModal(appt)}
                          className={`absolute inset-x-2 inset-y-2 rounded-[1.5rem] p-4 border-l-4 shadow-sm cursor-pointer z-10 transition-all hover:shadow-md hover:scale-[1.02] ${getStatusColor(appt.status)}`}
                        >
                          <div className="flex justify-between items-start mb-1">
                            <span className="text-[9px] font-black uppercase tracking-widest flex items-center gap-1 opacity-70">
                              {appt.status === 'confirmed' ? <Check size={10} /> : <Clock size={10} />}
                              {toHMLocal(appt.startLocal)}
                            </span>
                          </div>
                          <p className="font-black text-xs text-gray-800 leading-tight mb-1 truncate">{appt.title}</p>
                          <p className="text-[10px] font-bold opacity-60 uppercase tracking-tighter truncate">{appt.description}</p>
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
