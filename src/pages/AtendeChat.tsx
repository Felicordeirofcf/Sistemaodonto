import { useState, useRef, useEffect } from 'react';
import { Send, Bot, RefreshCw, AlertCircle, Paperclip, X, Image as ImageIcon, Sparkles } from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isError?: boolean;
  hasImage?: boolean;
  generatedImage?: string; // NOVO CAMPO: Para guardar a foto gerada pela IA
}

export function AtendeChat() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: 'Olá! Sou a Ana da OdontoSys. ✨\nEnvie uma foto do seu sorriso para eu fazer uma simulação!', sender: 'bot', timestamp: new Date() }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, imagePreview]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);
    }
  };

  const clearImage = () => {
    setSelectedImage(null);
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSendMessage = async () => {
    if (!inputText.trim() && !selectedImage) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      text: inputText || (selectedImage ? '📷 [Solicitação de Simulação]' : ''),
      sender: 'user',
      timestamp: new Date(),
      hasImage: !!selectedImage
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    const formData = new FormData();
    formData.append('message', inputText);
    if (selectedImage) {
      formData.append('image', selectedImage);
    }

    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (!response.ok) throw new Error(data.error || 'Erro no servidor');

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        sender: 'bot',
        timestamp: new Date(),
        generatedImage: data.image // SE TIVER IMAGEM, SALVA AQUI
      };
      setMessages(prev => [...prev, botMsg]);

    } catch (error: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: "Desculpe, tive uma instabilidade técnica. Tente novamente.",
        sender: 'bot',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      clearImage();
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <div className="flex-1 flex flex-col h-screen relative font-sans">
        
        {/* HEADER */}
        <header className="bg-white p-4 border-b border-gray-200 flex justify-between items-center shadow-sm z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center text-white shadow-md">
              <Bot size={24} />
            </div>
            <div>
              <h1 className="font-bold text-gray-800 text-lg">Ana - Estética Dental</h1>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse relative"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span></span>
                <span className="text-xs text-green-600 font-medium">IA Generativa</span>
              </div>
            </div>
          </div>
          <button onClick={() => setMessages([])} className="p-2 text-gray-400 hover:bg-gray-100 rounded-full"><RefreshCw size={20} /></button>
        </header>

        {/* CHAT AREA */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#e5ddd5]" style={{ backgroundImage: 'url("https://www.transparenttextures.com/patterns/subtle-white-feathers.png")' }}>
          
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
              
              {msg.sender === 'bot' && (
                 <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-pink-500 to-purple-600 flex items-center justify-center text-white shadow-sm mr-2 self-end mb-1"><Bot size={16} /></div>
              )}

              <div className={`max-w-[85%] p-4 rounded-2xl shadow-sm relative ${
                  msg.isError ? 'bg-red-50 text-red-800' : 
                  msg.sender === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white text-gray-800 rounded-bl-none'
                }`}>
                
                {/* --- AQUI É O SEGREDO: EXIBE A IMAGEM SE HOUVER --- */}
                {msg.generatedImage && (
                    <div className="mb-3 rounded-lg overflow-hidden border border-gray-100 shadow-sm">
                        <img src={msg.generatedImage} alt="Simulação IA" className="w-full h-auto max-h-80 object-cover" />
                        <div className="bg-purple-50 p-2 text-xs text-purple-700 text-center font-bold flex items-center justify-center gap-1">
                            <Sparkles size={12}/> Simulação Gerada por IA
                        </div>
                    </div>
                )}
                
                <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
               <div className="bg-white p-4 rounded-2xl rounded-bl-none shadow-sm flex items-center gap-2">
                 <Sparkles className="text-purple-500 animate-spin" size={16} />
                 <span className="text-sm text-gray-500">A IA está desenhando seu novo sorriso...</span>
               </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* FOOTER */}
        <div className="bg-white p-4 border-t border-gray-200 z-20">
          {imagePreview && (
            <div className="flex items-center gap-3 mb-3 bg-gray-50 p-2 rounded-lg border border-gray-100">
              <img src={imagePreview} className="h-16 w-16 object-cover rounded-md" />
              <button onClick={clearImage} className="bg-red-500 text-white rounded-full p-1"><X size={12} /></button>
            </div>
          )}

          <div className="flex items-end gap-2">
            <input type="file" accept="image/*" hidden ref={fileInputRef} onChange={handleImageSelect} />
            <button onClick={() => fileInputRef.current?.click()} className={`p-3 mb-1 rounded-full ${selectedImage ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}><Paperclip size={20} /></button>
            <textarea value={inputText} onChange={(e) => setInputText(e.target.value)} placeholder="Digite ou envie uma foto..." className="flex-1 bg-gray-100 rounded-2xl p-3 outline-none resize-none" rows={1} />
            <button onClick={handleSendMessage} disabled={isLoading} className="p-3 mb-1 rounded-full bg-blue-600 text-white"><Send size={20} /></button>
          </div>
        </div>
      </div>
    </div>
  );
}