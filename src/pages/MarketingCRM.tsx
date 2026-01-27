import { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';
import { MoreHorizontal, Plus, Phone, Calendar, X } from 'lucide-react';

interface Lead {
  id: number;
  name: string;
  source: string;
  phone?: string;
  status: string;
  notes?: string;
}

const COLUMNS = {
  new: { title: 'Novos Leads', color: 'border-blue-500', headerColor: 'text-blue-600' },
  contacted: { title: 'Agendamento Tentado', color: 'border-yellow-500', headerColor: 'text-yellow-600' },
  scheduled: { title: 'Consulta Agendada', color: 'border-green-500', headerColor: 'text-green-600' },
  treating: { title: 'Em Tratamento', color: 'border-purple-500', headerColor: 'text-purple-600' }
};

export function MarketingCRM() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newLead, setNewLead] = useState({ name: '', phone: '', source: 'Instagram', notes: '' });

  // Carregar Leads
  useEffect(() => {
    fetch('/api/marketing/leads', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('odonto_token')}` }
    })
      .then(res => res.json())
      .then(data => { if (Array.isArray(data)) setLeads(data); })
      .catch(console.error);
  }, []);

  // Salvar Novo Lead
  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        const res = await fetch('/api/marketing/leads', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
            },
            body: JSON.stringify(newLead)
        });
        const savedLead = await res.json();
        setLeads([...leads, savedLead]);
        setIsModalOpen(false);
        setNewLead({ name: '', phone: '', source: 'Instagram', notes: '' });
    } catch (error) {
        alert("Erro ao criar lead");
    }
  };

  const onDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const newStatus = destination.droppableId;
    const leadId = parseInt(draggableId);

    const oldLeads = [...leads];
    setLeads(prev => prev.map(l => l.id === leadId ? { ...l, status: newStatus } : l));

    try {
      await fetch(`/api/marketing/leads/${leadId}/move`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('odonto_token')}`
        },
        body: JSON.stringify({ status: newStatus })
      });
    } catch (error) {
      setLeads(oldLeads);
    }
  };

  const getColumnLeads = (status: string) => leads.filter(l => l.status === status);

  return (
    <div className="p-8 w-full h-screen overflow-hidden flex flex-col bg-gray-50 relative">
      <header className="flex justify-between items-end mb-6 flex-shrink-0">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Marketing & CRM</h1>
          <p className="text-gray-500 mt-1">Gestão de leads e funil de vendas.</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-bold hover:bg-blue-700 flex items-center gap-2 shadow-lg shadow-blue-200">
            <Plus size={18} /> Novo Lead
        </button>
      </header>

      {/* MODAL NOVO LEAD */}
      {isModalOpen && (
          <div className="absolute inset-0 z-50 bg-black/50 flex items-center justify-center backdrop-blur-sm">
              <div className="bg-white p-6 rounded-xl shadow-2xl w-96 animate-in fade-in zoom-in duration-200">
                  <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg font-bold">Novo Lead</h3>
                      <button onClick={() => setIsModalOpen(false)}><X size={20} className="text-gray-400" /></button>
                  </div>
                  <form onSubmit={handleCreateLead} className="flex flex-col gap-3">
                      <input required placeholder="Nome do Lead" className="p-2 border rounded" value={newLead.name} onChange={e => setNewLead({...newLead, name: e.target.value})} />
                      <input placeholder="WhatsApp (só números)" className="p-2 border rounded" value={newLead.phone} onChange={e => setNewLead({...newLead, phone: e.target.value})} />
                      <select className="p-2 border rounded" value={newLead.source} onChange={e => setNewLead({...newLead, source: e.target.value})}>
                          <option value="Instagram">Instagram</option>
                          <option value="Google">Google Ads</option>
                          <option value="Facebook">Facebook</option>
                          <option value="Indicação">Indicação</option>
                      </select>
                      <textarea placeholder="Notas iniciais..." className="p-2 border rounded" value={newLead.notes} onChange={e => setNewLead({...newLead, notes: e.target.value})} />
                      <button type="submit" className="bg-blue-600 text-white p-2 rounded font-bold mt-2">Salvar</button>
                  </form>
              </div>
          </div>
      )}

      <DragDropContext onDragEnd={onDragEnd}>
        <div className="flex-1 overflow-x-auto overflow-y-hidden pb-4">
          <div className="flex gap-6 h-full min-w-[1200px]">
            {Object.entries(COLUMNS).map(([columnId, config]) => {
              const columnItems = getColumnLeads(columnId);
              return (
                <div key={columnId} className="flex flex-col bg-gray-100/50 rounded-xl w-80 h-full max-h-full border border-gray-200">
                  <div className={`bg-white p-4 rounded-t-xl border-b border-gray-100 flex justify-between items-center border-t-4 ${config.color}`}>
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${config.headerColor}`}>{config.title}</span>
                      <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full font-bold">{columnItems.length}</span>
                    </div>
                  </div>
                  <Droppable droppableId={columnId}>
                    {(provided, snapshot) => (
                      <div {...provided.droppableProps} ref={provided.innerRef} className={`flex-1 p-3 flex flex-col gap-3 overflow-y-auto transition-colors ${snapshot.isDraggingOver ? 'bg-blue-50/50' : ''}`}>
                        {columnItems.map((item, index) => (
                          <Draggable key={item.id} draggableId={item.id.toString()} index={index}>
                            {(provided, snapshot) => (
                              <div ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} className={`bg-white p-4 rounded-lg border border-gray-100 group hover:border-blue-300 transition-all ${snapshot.isDragging ? 'shadow-2xl rotate-2 scale-105 z-50' : 'shadow-sm'}`} style={provided.draggableProps.style}>
                                <div className="flex justify-between items-start mb-2"><div className="font-bold text-gray-800">{item.name}</div><MoreHorizontal size={16} className="text-gray-300" /></div>
                                <div className="flex items-center gap-1 text-xs text-gray-500 mb-3"><div className={`w-2 h-2 rounded-full ${item.source === 'Instagram' ? 'bg-purple-500' : 'bg-blue-500'}`}></div>{item.source}</div>
                                {item.notes && <div className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 p-2 rounded mb-3"><Calendar size={12} /> {item.notes}</div>}
                                <div className="flex justify-between items-center pt-3 border-t border-gray-50">
                                   <button className="text-xs font-bold text-green-600 flex items-center gap-1 hover:bg-green-50 px-2 py-1 rounded" onClick={() => window.open(`https://wa.me/55${item.phone}`, '_blank')}><Phone size={12} /> WhatsApp</button>
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </div>
              );
            })}
          </div>
        </div>
      </DragDropContext>
    </div>
  );
}