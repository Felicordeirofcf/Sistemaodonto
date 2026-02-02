// whatsapp-qr-service/server.js
import express from "express";
import qrcode from "qrcode";
import pkg from "whatsapp-web.js";
const { Client, LocalAuth } = pkg;

// Se você instalou "puppeteer" (recomendado), ele fornece o Chromium.
// Isso evita o erro "Could not find Chrome" no Render.
let puppeteer = null;
try {
  puppeteer = await import("puppeteer");
} catch {
  // se não tiver puppeteer instalado, o whatsapp-web.js vai tentar usar puppeteer-core
  // e provavelmente vai falhar no Render por falta de Chrome.
}

const app = express();
app.use(express.json({ limit: "1mb" }));

// CORS básico (debug)
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, X-Internal-Secret");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  if (req.method === "OPTIONS") return res.sendStatus(200);
  next();
});

const PORT = Number(process.env.PORT || 3333);

const FLASK_WEBHOOK_URL =
  process.env.FLASK_WEBHOOK_URL ||
  "http://localhost:5000/api/marketing/whatsapp/webhook-incoming";

const INTERNAL_WEBHOOK_SECRET = process.env.INTERNAL_WEBHOOK_SECRET || "dev_secret";
const CLINIC_ID = Number(process.env.CLINIC_ID || 1);

// Cache dir recomendado no Render (pode ajustar pelo ENV)
process.env.PUPPETEER_CACHE_DIR =
  process.env.PUPPETEER_CACHE_DIR || "/opt/render/.cache/puppeteer";

// Se você quiser forçar download no build:
process.env.PUPPETEER_SKIP_DOWNLOAD = process.env.PUPPETEER_SKIP_DOWNLOAD ?? "false";

let status = "connecting"; // connected | disconnected | connecting
let lastQRBase64 = null;
let lastError = null;

function getExecutablePathSafe() {
  try {
    if (puppeteer?.executablePath) {
      return puppeteer.executablePath();
    }
  } catch {}
  return undefined;
}

const executablePath = getExecutablePathSafe();
if (executablePath) {
  console.log("✅ Puppeteer Chromium path:", executablePath);
} else {
  console.log("⚠️ Puppeteer executablePath não disponível. Verifique se 'puppeteer' está instalado.");
}

const client = new Client({
  authStrategy: new LocalAuth({ clientId: `clinic-${CLINIC_ID}` }),
  puppeteer: {
    headless: true,
    executablePath, // <- chave para Render (quando puppeteer está instalado)
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--no-zygote",
      "--single-process"
    ]
  }
});

client.on("qr", async (qr) => {
  try {
    status = "connecting";
    lastQRBase64 = await qrcode.toDataURL(qr);
    lastError = null;
    console.log("📲 QR gerado (aguardando scan)...");
  } catch (e) {
    lastError = "Falha ao gerar QR";
    console.log("❌ Erro ao gerar QR:", e?.message || e);
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

async function postJSON(url, data, headers = {}) {
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(data)
    });
    return { ok: resp.ok, status: resp.status };
  } catch (e) {
    return { ok: false, status: 0, error: e?.message || "fetch_failed" };
  }
}

client.on("message", async (message) => {
  try {
    // message.from pode ser: "551199...@c.us" (contato) ou "xxxxx@g.us" (grupo)
    const fromRaw = message.from || "";
    const isGroup = fromRaw.endsWith("@g.us");
    const from = fromRaw.replace("@c.us", "").replace("@g.us", "");

    const body = message.body || "";

    await postJSON(
      FLASK_WEBHOOK_URL,
      {
        clinic_id: CLINIC_ID,
        from,
        body,
        is_group: isGroup,
        raw_from: fromRaw,
        timestamp: Date.now()
      },
      { "X-Internal-Secret": INTERNAL_WEBHOOK_SECRET }
    );
  } catch {
    // silencioso no MVP
  }
});

app.get("/health", (req, res) => {
  res.json({
    ok: true,
    status,
    clinic_id: CLINIC_ID,
    has_qr: Boolean(lastQRBase64),
    last_error: lastError,
    webhook: FLASK_WEBHOOK_URL
  });
});

app.get("/qr", (req, res) => {
  res.json({
    status,
    qr_base64: lastQRBase64
  });
});

// Envio para contato (número) ou grupo (id@g.us)
app.post("/send", async (req, res) => {
  const { to, message } = req.body || {};

  if (!to || !message) {
    return res.status(400).json({ ok: false, message: "to e message obrigatórios" });
  }

  if (status !== "connected") {
    return res.status(409).json({ ok: false, message: "WhatsApp não está conectado" });
  }

  try {
    const toStr = String(to).trim();

    // Se já vier com @c.us ou @g.us, respeita.
    const chatId =
      toStr.endsWith("@c.us") || toStr.endsWith("@g.us")
        ? toStr
        : `${toStr}@c.us`;

    await client.sendMessage(chatId, String(message));
    return res.json({ ok: true });
  } catch (e) {
    return res.status(500).json({ ok: false, message: e?.message || "Falha ao enviar" });
  }
});

// (Opcional) reset de sessão (use com cuidado)
app.post("/pairing/reset", async (req, res) => {
  try {
    lastQRBase64 = null;
    lastError = null;
    status = "connecting";

    // Desconecta / reinicializa
    try { await client.logout(); } catch {}
    try { await client.destroy(); } catch {}

    // Recria sessão
    setTimeout(() => client.initialize(), 1500);

    return res.json({ ok: true });
  } catch (e) {
    return res.status(500).json({ ok: false, message: e?.message || "Erro ao resetar" });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 WhatsApp QR Service rodando na porta ${PORT}`);
  console.log("FLASK_WEBHOOK_URL:", FLASK_WEBHOOK_URL);
  console.log("CLINIC_ID:", CLINIC_ID);
});

client.initialize();
