import { useState, useRef, useEffect } from 'react';
import { Send, Bot, RefreshCw, AlertCircle } from 'lucide-react';
import { GoogleGenerativeAI } from '@google/generative-ai';

// --- CONFIGURAÇÃO DA IA ---
// Recomendação: Use import.meta.env.VITE_GEMINI_API_KEY para maior segurança
const apiKey = import.meta.env.VITE_GEMINI_API_KEY;

const MODEL_NAME = "gemini-2.5-flash";
const genAI = new GoogleGenerativeAI(apiKey);

const SYSTEM_PROMPT = `
Você é a Ana, assistente virtual da clínica OdontoSys.
Seu tom é: Simpático, acolhedor e profissional. Use emojis moderadamente.
Seu objetivo: Agendar consultas ou tirar dúvidas sobre tratamentos.

Informações da Clínica:
- Horário: Seg a Sex das 09:00 às 18:00.
- Tratamentos: Limpeza, Clareamento, Implante, Harmonização Facial.
- Preços: A avaliação custa R$ 100,00. Outros procedimentos dependem de avaliação.

Regras de Agendamento (Simulado):
- Ofereça horários para amanhã ou depois.
- Se o cliente confirmar, diga: "Agendado! Vou passar para o Dr. Fonseca."
- Seja breve (máximo 3 frases).
`;

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isError?: boolean;
}

export function AtendeChat() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: 'Olá! Sou a Ana da OdontoSys. Como posso ajudar seu sorriso hoje? ✨', sender: 'bot', timestamp: new Date() }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const model = genAI.getGenerativeModel({ 
        model: MODEL_NAME,
        systemInstruction: SYSTEM_PROMPT 
      });
      
      // CORREÇÃO DO HISTÓRICO:
      // 1. Filtramos erros.
      // 2. A primeira mensagem do histórico DEVE ser do 'user'.
      // Como a primeira mensagem da lista é o bot (saudação), nós a ignoramos no histórico enviado à API.
      const chatHistory = messages
        .filter(m => !m.isError && m.id !== '1') // Ignora a saudação inicial e erros
        .map(m => ({
          role: m.sender === 'user' ? 'user' : 'model',
          parts: [{ text: m.text }],
        }));

      const chat = model.startChat({
        history: chatHistory,
      });

      const result = await chat.sendMessage(inputText);
      const response = await result.response;
      const text = response.text();

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: text,
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMsg]);

    } catch (error: any) {
      console.error("Erro na IA:", error);
      let errorText = "Desculpe, tive um erro de conexão.";
      
      if (error.message?.includes('role')) {
        errorText = "Erro de sincronização no chat. Tente reiniciar a conversa.";
      } else if (error.message?.includes('429')) {
        errorText = "Muitas mensagens! Aguarde 1 minuto e tente novamente.";
      }

      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: errorText,
        sender: 'bot',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <div className="flex-1 flex flex-col h-screen">
        <header className="bg-white p-4 border-b border-gray-200 flex justify-between items-center shadow-sm z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center text-white">
              <Bot size={24} />
            </div>
            <div>
              <h1 className="font-bold text-gray-800">AtendeChat AI</h1>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-xs text-green-600 font-medium">Ana Online</span>
              </div>
            </div>
          </div>
          <button 
            onClick={() => setMessages([{ id: '1', text: 'Olá! Sou a Ana da OdontoSys. Como posso ajudar seu sorriso hoje? ✨', sender: 'bot', timestamp: new Date() }])}
            className="p-2 text-gray-500 hover:bg-gray-100 rounded-full"
            title="Reiniciar conversa"
          >
            <RefreshCw size={20} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[#e5ddd5]" 
             style={{ backgroundImage: 'url("https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png")', backgroundRepeat: 'repeat' }}>
          
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[70%] p-3 rounded-lg shadow-sm relative ${
                  msg.isError 
                    ? 'bg-red-100 text-red-800 border border-red-200'
                    : msg.sender === 'user'
                      ? 'bg-[#dcf8c6] text-gray-800 rounded-tr-none'
                      : 'bg-white text-gray-800 rounded-tl-none'
                }`}
              >
                {msg.isError && <div className="flex items-center gap-2 mb-1 font-bold"><AlertCircle size={14}/> Erro</div>}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                <span className="text-[10px] opacity-60 block text-right mt-1">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
               <div className="bg-white p-3 rounded-lg rounded-tl-none shadow-sm flex gap-1 items-center">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></div>
               </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="bg-gray-50 p-4 border-t border-gray-200">
          <div className="bg-white rounded-full flex items-center px-4 py-2 border border-gray-300 shadow-sm focus-within:ring-2 focus-within:ring-blue-500 transition-shadow">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Digite uma mensagem..."
              className="flex-1 bg-transparent outline-none text-gray-700 placeholder-gray-400"
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputText.trim()}
              className={`ml-2 p-2 rounded-full transition-colors ${
                inputText.trim() ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-200 text-gray-400'
              }`}
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            AI Powered by Google Gemini 2.5 Flash
          </p>
        </div>
      </div>
    </div>
  );
}