// whatsapp-qr-service/server.js
import express from "express";
import qrcode from "qrcode";
import { Client, LocalAuth } from "whatsapp-web.js";

const app = express();
app.use(express.json());

// (Opcional) CORS básico p/ debug
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, X-Internal-Secret");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  if (req.method === "OPTIONS") return res.sendStatus(200);
  next();
});

const PORT = process.env.PORT || 3333;

// URL do seu backend Flask para receber mensagens que chegarem no WhatsApp
const FLASK_WEBHOOK_URL =
  process.env.FLASK_WEBHOOK_URL ||
  "http://localhost:5000/api/marketing/whatsapp/webhook-incoming";

const INTERNAL_WEBHOOK_SECRET = process.env.INTERNAL_WEBHOOK_SECRET || "dev_secret";

// No seu caso: 1 clínica
const CLINIC_ID = Number(process.env.CLINIC_ID || 1);

// ===== Estado do serviço =====
let status = "connecting"; // connected | connecting | disconnected
let lastQRBase64 = null;
let lastError = null;

// ===== Inicializa WhatsApp Web =====
const client = new Client({
  authStrategy: new LocalAuth({ clientId: `clinic-${CLINIC_ID}` }),
  puppeteer: {
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu"
    ]
  }
});

client.on("qr", async (qr) => {
  try {
    status = "connecting";
    lastQRBase64 = await qrcode.toDataURL(qr);
    lastError = null;
  } catch (e) {
    lastError = "Falha ao gerar QR";
  }
});

client.on("ready", () => {
  status = "connected";
  lastQRBase64 = null;
  lastError = null;
  console.log("✅ WhatsApp client READY");
});

client.on("authenticated", () => {
  console.log("✅ WhatsApp authenticated");
});

client.on("auth_failure", (msg) => {
  status = "disconnected";
  lastError = `auth_failure: ${msg || "unknown"}`;
  console.log("❌ auth_failure:", msg);
});

client.on("disconnected", (reason) => {
  status = "disconnected";
  lastError = `disconnected: ${reason || "unknown"}`;
  console.log("⚠️ disconnected:", reason);
});

// Helper: POST simples sem node-fetch
async function postJSON(url, data, headers = {}) {
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(data)
    });
    // não quebra se response não for json
    return { ok: resp.ok, status: resp.status };
  } catch (e) {
    return { ok: false, status: 0 };
  }
}

// Quando chega mensagem no WhatsApp
client.on("message", async (message) => {
  try {
    const from = (message.from || "").replace("@c.us", "");
    const body = message.body || "";

    // encaminha pro Flask (não trava se falhar)
    await postJSON(
      FLASK_WEBHOOK_URL,
      { clinic_id: CLINIC_ID, from, body, timestamp: Date.now() },
      { "X-Internal-Secret": INTERNAL_WEBHOOK_SECRET }
    );
  } catch (e) {
    // silencioso no MVP
  }
});

// ===== Rotas HTTP do serviço =====

app.get("/health", (req, res) => {
  res.json({
    ok: true,
    status,
    clinic_id: CLINIC_ID,
    has_qr: Boolean(lastQRBase64),
    last_error: lastError
  });
});

app.get("/qr", (req, res) => {
  res.json({
    status,
    qr_base64: lastQRBase64
  });
});

app.post("/send", async (req, res) => {
  const { to, message } = req.body || {};

  if (!to || !message) {
    return res.status(400).json({ ok: false, message: "to e message obrigatórios" });
  }

  if (status !== "connected") {
    return res.status(409).json({ ok: false, message: "WhatsApp não está conectado" });
  }

  try {
    // whatsapp-web.js usa formato: 55dddnumero@c.us
    const chatId = `${String(to).trim()}@c.us`;
    await client.sendMessage(chatId, String(message));
    return res.json({ ok: true });
  } catch (e) {
    return res.status(500).json({ ok: false, message: "Falha ao enviar" });
  }
});

// Start
app.listen(PORT, () => {
  console.log(`🚀 WhatsApp QR Service rodando na porta ${PORT}`);
  console.log("FLASK_WEBHOOK_URL:", FLASK_WEBHOOK_URL);
});

// Inicializa o client
client.initialize();
