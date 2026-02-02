// src/pages/WhatsAppModulePage.tsx
import React, { useEffect, useState } from "react";
import { RefreshCcw, Send, PlugZap, ShieldAlert } from "lucide-react";

type QRStatus = {
  status: "connected" | "disconnected" | "connecting";
  qr_base64?: string;
  last_update?: string;
  error?: string;
};

type ApiResult = { ok: boolean; message?: string };

const API_BASE = import.meta.env.VITE_API_URL || "";
const API = (path: string) => `${API_BASE}${path}`;

function authHeaders() {
  const token = localStorage.getItem("odonto_token"); // ✅ token correto
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

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

  const [authProblem, setAuthProblem] = useState<string | null>(null);

  async function fetchQR() {
    setAuthProblem(null);

    try {
      setLoadingQR(true);

      const res = await fetch(API("/api/marketing/whatsapp/qr"), {
        headers: authHeaders(),
      });

      if (res.status === 401 || res.status === 422) {
        setAuthProblem("Sua sessão expirou ou você não está autenticado. Faça login novamente.");
        setQr({ status: "disconnected" });
        return;
      }

      const data = await res.json();
      setQr(data);
    } catch {
      setQr({ status: "disconnected", error: "Falha de rede ao buscar QR." });
    } finally {
      setLoadingQR(false);
    }
  }

  async function sendTest() {
    setSendResult(null);
    setAuthProblem(null);
    setSending(true);

    try {
      const res = await fetch(API("/api/marketing/whatsapp/send"), {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ to, message: msg }),
      });

      if (res.status === 401 || res.status === 422) {
        setAuthProblem("Sua sessão expirou ou você não está autenticado. Faça login novamente.");
        setSendResult({ ok: false, message: "Não autenticado" });
        return;
      }

      const data = await res.json();
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
    setAuthProblem(null);

    try {
      const res = await fetch(API("/api/marketing/whatsapp/recall/config"), {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ days: recallDays, hour: recallHour }),
      });

      if (res.status === 401 || res.status === 422) {
        setAuthProblem("Sua sessão expirou ou você não está autenticado. Faça login novamente.");
        setRecallSaved("Não autenticado");
        return;
      }

      const data = await res.json();
      setRecallSaved(data?.ok ? "Configuração salva ✅" : data?.message || "Erro ao salvar");
    } catch {
      setRecallSaved("Erro ao salvar");
    } finally {
      setSavingRecall(false);
    }
  }

  useEffect(() => {
    fetchQR();
    const t = setInterval(fetchQR, 12000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen w-full bg-[#070B14] text-slate-100">
      <div className="px-6 py-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold tracking-wide">WhatsApp</h1>
            <p className="text-sm text-slate-400">
              Conexão por QR (teste), envio manual e regras de recall automatizado.
            </p>
          </div>

          <button
            onClick={fetchQR}
            disabled={loadingQR}
            className="inline-flex items-center gap-2 rounded-xl bg-[#1C2B4A] px-4 py-2 text-sm hover:bg-[#24365B] disabled:opacity-60"
          >
            <RefreshCcw size={16} />
            Atualizar
          </button>
        </div>

        {authProblem && (
          <div className="mt-4 rounded-xl border border-yellow-800 bg-yellow-900/20 p-3 text-sm text-yellow-200">
            {authProblem}
          </div>
        )}

        {qr?.error && (
          <div className="mt-4 rounded-xl border border-rose-800 bg-rose-900/20 p-3 text-sm text-rose-200">
            {qr.error}
          </div>
        )}

        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* STATUS + QR */}
          <div className="rounded-2xl border border-slate-800 bg-[#0B1220] p-4 lg:col-span-1">
            <div className="flex items-center gap-2">
              <PlugZap size={18} className="text-[#2D6BFF]" />
              <h2 className="text-base font-semibold">Conexão</h2>
            </div>

            <div className="mt-3 flex items-center gap-2 text-sm">
              <span className="text-slate-400">Status:</span>
              <span
                className={
                  qr.status === "connected"
                    ? "text-emerald-400"
                    : qr.status === "connecting"
                    ? "text-yellow-300"
                    : "text-rose-400"
                }
              >
                {qr.status === "connected"
                  ? "Conectado"
                  : qr.status === "connecting"
                  ? "Conectando"
                  : "Desconectado"}
              </span>
            </div>

            {qr.status !== "connected" && (
              <div className="mt-4">
                <p className="text-xs text-slate-400">
                  Escaneie o QR com o WhatsApp (Aparelhos conectados).
                </p>

                <div className="mt-3 flex items-center justify-center rounded-2xl bg-[#070B14] p-3">
                  {qr.qr_base64 ? (
                    <img src={qr.qr_base64} alt="QR Code WhatsApp" className="h-56 w-56 rounded-xl" />
                  ) : (
                    <div className="flex h-56 w-56 items-center justify-center text-xs text-slate-500">
                      QR ainda não disponível…
                    </div>
                  )}
                </div>

                <div className="mt-3 flex items-start gap-2 rounded-xl border border-slate-800 bg-[#0F1A2B] p-3 text-xs text-slate-300">
                  <ShieldAlert size={16} className="mt-[2px] text-yellow-300" />
                  <p>Modo QR é só para testes. Para produção, o ideal é migrar para WhatsApp Business API.</p>
                </div>
              </div>
            )}

            {qr.status === "connected" && (
              <div className="mt-4 rounded-xl border border-slate-800 bg-[#0F1A2B] p-3 text-sm text-slate-200">
                Conectado ✅ Você já pode enviar mensagens.
              </div>
            )}
          </div>

          {/* ENVIO TESTE */}
          <div className="rounded-2xl border border-slate-800 bg-[#0B1220] p-4 lg:col-span-2">
            <h2 className="text-base font-semibold">Envio de teste</h2>
            <p className="mt-1 text-xs text-slate-400">Use número no formato internacional (ex.: 55DDDNUMERO).</p>

            <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-3">
              <div className="lg:col-span-1">
                <label className="text-xs text-slate-400">Enviar para</label>
                <input
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  placeholder="5599999999999"
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2 text-sm outline-none focus:border-[#2D6BFF]"
                />
              </div>

              <div className="lg:col-span-2">
                <label className="text-xs text-slate-400">Mensagem</label>
                <textarea
                  value={msg}
                  onChange={(e) => setMsg(e.target.value)}
                  rows={3}
                  className="mt-1 w-full resize-none rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2 text-sm outline-none focus:border-[#2D6BFF]"
                />
              </div>
            </div>

            <div className="mt-3 flex items-center gap-3">
              <button
                onClick={sendTest}
                disabled={sending || !to || !msg}
                className="inline-flex items-center gap-2 rounded-xl bg-[#2D6BFF] px-4 py-2 text-sm font-semibold text-white hover:brightness-110 disabled:opacity-60"
              >
                <Send size={16} />
                {sending ? "Enviando..." : "Enviar"}
              </button>

              {sendResult && (
                <span className={`text-sm ${sendResult.ok ? "text-emerald-400" : "text-rose-400"}`}>
                  {sendResult.ok ? "Enviado ✅" : `Erro: ${sendResult.message || "falha"}`}
                </span>
              )}
            </div>
          </div>

          {/* CONFIG RECALL */}
          <div className="rounded-2xl border border-slate-800 bg-[#0B1220] p-4 lg:col-span-3">
            <h2 className="text-base font-semibold">Recall automático (reativação)</h2>
            <p className="mt-1 text-xs text-slate-400">
              Ex.: após 30 dias sem interação, mandar uma mensagem para captar retorno.
            </p>

            <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-6">
              <div className="lg:col-span-2">
                <label className="text-xs text-slate-400">Dias sem contato</label>
                <input
                  type="number"
                  min={7}
                  max={365}
                  value={recallDays}
                  onChange={(e) => setRecallDays(Number(e.target.value))}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2 text-sm outline-none focus:border-[#2D6BFF]"
                />
              </div>

              <div className="lg:col-span-2">
                <label className="text-xs text-slate-400">Horário de disparo</label>
                <input
                  type="time"
                  value={recallHour}
                  onChange={(e) => setRecallHour(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-800 bg-[#070B14] px-3 py-2 text-sm outline-none focus:border-[#2D6BFF]"
                />
              </div>

              <div className="lg:col-span-2 flex items-end gap-3">
                <button
                  onClick={saveRecallConfig}
                  disabled={savingRecall}
                  className="rounded-xl bg-[#1C2B4A] px-4 py-2 text-sm hover:bg-[#24365B] disabled:opacity-60"
                >
                  {savingRecall ? "Salvando..." : "Salvar configuração"}
                </button>
                {recallSaved && <span className="text-sm text-slate-200">{recallSaved}</span>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
