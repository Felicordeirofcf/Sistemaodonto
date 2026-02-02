import React, { useEffect, useState } from "react";
import { RefreshCcw, Send, PlugZap, ShieldAlert, Smartphone } from "lucide-react";

// Tipagem atualizada para aceitar a mensagem do Backend
type QRStatus = {
  status: "connected" | "disconnected" | "connecting";
  qr_base64?: string;
  message?: string; // Nova mensagem de status (ex: "Aguarde...")
  last_update?: string;
  warning?: string;
};

type ApiResult = { ok: boolean; message?: string };

const API_BASE = import.meta.env.VITE_API_URL || "";
const API = (path: string) => `${API_BASE}${path}`;

export function WhatsAppModulePage() {
  const [qr, setQr] = useState<QRStatus>({ status: "connecting" });
  const [loadingQR, setLoadingQR] = useState(false);

  const [to, setTo] = useState("");
  const [msg, setMsg] = useState("Olá! Aqui é a recepção 😊 Posso te ajudar a agendar um horário?");
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<ApiResult | null>(null);

  const [recallDays, setRecallDays] = useState(30);
  const [recallHour, setRecallHour] = useState("09:00");
  const [savingRecall, setSavingRecall] = useState(false);
  const [recallSaved, setRecallSaved] = useState<string | null>(null);

  function getHeaders() {
    const token = localStorage.getItem("odonto_token");
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  async function fetchQR() {
    try {
      // Não ativamos o loading visual total para não piscar a tela no polling
      const res = await fetch(API("/api/marketing/whatsapp/qr"), { headers: getHeaders() });

      if (!res.ok) {
        const txt = await res.text();
        setQr((prev) => ({ ...prev, warning: `Erro ${res.status}: ${txt}` }));
        return;
      }

      const data = await res.json();
      setQr(data);
    } catch (e: any) {
      console.error(e);
      // Não sobrescrevemos tudo com erro para não perder o QR code se a rede piscar
    }
  }

  // Função manual com loading visual
  async function handleManualRefresh() {
    setLoadingQR(true);
    await fetchQR();
    setLoadingQR(false);
  }

  async function sendTest() {
    setSendResult(null);
    setSending(true);
    
    // Limpeza básica do número (remove () - e espaços)
    const cleanTo = to.replace(/\D/g, "");

    try {
      const res = await fetch(API("/api/marketing/whatsapp/send"), {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ to: cleanTo, message: msg }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setSendResult({ ok: false, message: data?.message || `Erro ${res.status}` });
        return;
      }
      setSendResult(data);
    } catch {
      setSendResult({ ok: false, message: "Falha ao enviar." });
    } finally {
      setSending(false);
    }
  }

  async function saveRecallConfig() {
    setSavingRecall(true);
    setRecallSaved(null);
    try {
      const res = await fetch(API("/api/marketing/whatsapp/recall/config"), {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ days: recallDays, hour: recallHour }),
      });
      const data = await res.json().catch(() => ({}));
      setRecallSaved(res.ok && data?.ok ? "Configuração salva ✅" : data?.message || "Erro ao salvar");
    } catch {
      setRecallSaved("Erro ao salvar");
    } finally {
      setSavingRecall(false);
    }
  }

  useEffect(() => {
    fetchQR();
    // Atualizado para 5 segundos (Backend tem cache agora, então é seguro e mais rápido)
    const t = setInterval(fetchQR, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen w-full bg-[#070B14] text-slate-100">
      <div className="px-6 py-6">
        {/* CABEÇALHO */}
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold tracking-wide">WhatsApp</h1>
            <p className="text-sm text-slate-400">
              Gerenciamento de conexão e disparos automáticos.
            </p>
          </div>

          <button
            onClick={handleManualRefresh}
            disabled={loadingQR}
            className="inline-flex items-center gap-2 rounded-xl bg-[#1C2B4A] px-4 py-2 text-sm hover:bg-[#24365B] disabled:opacity-60 transition-colors"
          >
            <RefreshCcw size={16} className={loadingQR ? "animate-spin" : ""} />
            {loadingQR ? "Carregando..." : "Atualizar"}
          </button>
        </div>

        {/* AVISO DE ERRO */}
        {qr.warning && (
          <div className="mt-4 rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-3 text-xs text-yellow-200">
            ⚠ {qr.warning}
          </div>
        )}

        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          
          {/* CARTÃO 1: CONEXÃO E QR CODE */}
          <div className="rounded-2xl border border-slate-800 bg-[#0B1220] p-4 lg:col-span-1 flex flex-col h-full">
            <div className="flex items-center gap-2 mb-4">
              <PlugZap size={18} className="text-[#2D6BFF]" />
              <h2 className="text-base font-semibold">Status da Conexão</h2>
            </div>

            <div className="flex flex-col items-center justify-center flex-1">
              {/* Indicador de Status */}
              <div className={`mb-4 flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium border ${
                qr.status === "connected" 
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" 
                  : qr.status === "connecting"
                  ? "bg-yellow-500/10 border-yellow-500/20 text-yellow-300"
                  : "bg-rose-500/10 border-rose-500/20 text-rose-400"
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  qr.status === "connected" ? "bg-emerald-400 animate-pulse" : qr.status === "connecting" ? "bg-yellow-300" : "bg-rose-400"
                }`} />
                {qr.status === "connected"
                  ? "Online e Pronto"
                  : qr.status === "connecting"
                  ? "Iniciando..."
                  : "Desconectado"}
              </div>

              {/* Área do QR Code */}
              {qr.status !== "connected" && (
                <div className="flex flex-col items-center animate-in fade-in duration-500">
                  <div className="relative flex items-center justify-center rounded-2xl bg-white p-2 shadow-lg shadow-black/50">
                    {qr.qr_base64 ? (
                      <img src={qr.qr_base64} alt="QR Code WhatsApp" className="h-52 w-52 rounded-lg" />
                    ) : (
                      <div className="flex h-52 w-52 flex-col items-center justify-center gap-3 bg-slate-100 text-slate-400 rounded-lg">
                        <RefreshCcw className="animate-spin text-slate-300" size={32} />
                        <span className="text-xs font-medium text-slate-500">
                          {qr.message || "Buscando QR Code..."}
                        </span>
                      </div>
                    )}
                    
                    {/* Overlay de mensagem se houver (ex: "Aguarde...") */}
                    {!qr.qr_base64 && qr.message && (
                      <div className="absolute inset-0 flex items-center justify-center bg-white/80 rounded-lg">
                        <span className="text-xs font-bold text-slate-600 animate-pulse">{qr.message}</span>
                      </div>
                    )}
                  </div>
                  
                  <p className="mt-4 text-center text-xs text-slate-400 max-w-[200px]">
                    Abra o WhatsApp no seu celular &gt; Aparelhos conectados &gt; Conectar aparelho.
                  </p>
                </div>
              )}

              {/* Mensagem de Conectado */}
              {qr.status === "connected" && (
                <div className="flex flex-col items-center justify-center py-10 text-emerald-500/80">
                  <Smartphone size={64} strokeWidth={1.5} />
                  <p className="mt-4 text-sm font-medium text-slate-300">Sessão ativa com sucesso</p>
                </div>
              )}
            </div>

            <div className="mt-auto pt-4">
               {qr.status !== "connected" && (
                <div className="flex items-start gap-2 rounded-xl border border-slate-800 bg-[#0F1A2B] p-3 text-xs text-slate-400">
                  <ShieldAlert size={16} className="mt-[2px] text-blue-400 shrink-0" />
                  <p>O QR Code pode levar até 40s para carregar na primeira vez.</p>
                </div>
               )}
            </div>
          </div>

          {/* COLUNA DA DIREITA: TESTE E CONFIGURAÇÃO */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            
            {/* CARTÃO 2: ENVIO DE TESTE */}
            <div className="rounded-2xl border border-slate-800 bg-[#0B1220] p-5">
              <h2 className="text-base font-semibold flex items-center gap-2">
                <Send size={18} className="text-[#2D6BFF]" />
                Envio de teste
              </h2>
              <p className="mt-1 text-xs text-slate-400">Valide se as mensagens estão chegando corretamente.</p>

              <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
                <div className="lg:col-span-1">
                  <label className="text-xs font-medium text-slate-400 ml-1">Whatsapp de Destino</label>
                  <input
                    value={to}
                    onChange={(e) => setTo(e.target.value)}
                    placeholder="Ex: 5511999999999"
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2.5 text-sm outline-none focus:border-[#2D6BFF] transition-all placeholder:text-slate-600"
                  />
                </div>

                <div className="lg:col-span-2">
                  <label className="text-xs font-medium text-slate-400 ml-1">Mensagem</label>
                  <div className="flex gap-2 mt-1">
                    <input
                      value={msg}
                      onChange={(e) => setMsg(e.target.value)}
                      className="w-full rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2.5 text-sm outline-none focus:border-[#2D6BFF] transition-all"
                    />
                    <button
                      onClick={sendTest}
                      disabled={sending || !to || !msg || qr.status !== "connected"}
                      className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#2D6BFF] px-6 py-2 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all whitespace-nowrap"
                    >
                      {sending ? "..." : <Send size={16} />}
                      {sending ? "Enviando" : "Enviar"}
                    </button>
                  </div>
                </div>
              </div>

              {sendResult && (
                <div className={`mt-3 flex items-center gap-2 text-xs font-medium px-3 py-2 rounded-lg ${
                  sendResult.ok ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                }`}>
                   {sendResult.ok ? "✅ Mensagem enviada com sucesso!" : `❌ Erro: ${sendResult.message}`}
                </div>
              )}
            </div>

            {/* CARTÃO 3: RECALL */}
            <div className="rounded-2xl border border-slate-800 bg-[#0B1220] p-5 flex-1">
              <h2 className="text-base font-semibold flex items-center gap-2">
                <RefreshCcw size={18} className="text-purple-400" />
                Recall automático (Reativação)
              </h2>
              <p className="mt-1 text-xs text-slate-400">Configure quando o sistema deve tentar reativar pacientes sumidos.</p>

              <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-6 items-end">
                <div className="lg:col-span-2">
                  <label className="text-xs font-medium text-slate-400 ml-1">Dias sem interação</label>
                  <input
                    type="number"
                    min={1}
                    max={365}
                    value={recallDays}
                    onChange={(e) => setRecallDays(Number(e.target.value))}
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2.5 text-sm outline-none focus:border-purple-500 transition-all"
                  />
                </div>

                <div className="lg:col-span-2">
                  <label className="text-xs font-medium text-slate-400 ml-1">Horário de disparo</label>
                  <input
                    type="time"
                    value={recallHour}
                    onChange={(e) => setRecallHour(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2.5 text-sm outline-none focus:border-purple-500 transition-all"
                  />
                </div>

                <div className="lg:col-span-2">
                  <button
                    onClick={saveRecallConfig}
                    disabled={savingRecall}
                    className="w-full rounded-xl bg-[#1C2B4A] px-4 py-2.5 text-sm font-medium hover:bg-[#24365B] disabled:opacity-60 transition-colors text-purple-200"
                  >
                    {savingRecall ? "Salvando..." : "Salvar Configuração"}
                  </button>
                </div>
              </div>
               {recallSaved && (
                <p className="mt-3 text-xs text-center text-slate-400 animate-pulse">
                  {recallSaved}
                </p>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}