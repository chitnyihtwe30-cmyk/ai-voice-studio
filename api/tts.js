const MODEL = 'gemini-3.1-flash-tts-preview';
const MAX_CHARS = 2600; // Internal Gemini chunk size; users are not limited by this.
const MAX_RETRIES = 2;

function chunkText(text) {
  const chunks = [];
  let rest = text.trim();
  while (rest.length > MAX_CHARS) {
    let cut = rest.lastIndexOf('။', MAX_CHARS);
    if (cut < MAX_CHARS * 0.55) cut = rest.lastIndexOf(' ', MAX_CHARS);
    if (cut < MAX_CHARS * 0.55) cut = MAX_CHARS;
    const end = cut + (rest[cut] === '။' ? 1 : 0);
    chunks.push(rest.slice(0, end).trim());
    rest = rest.slice(end).trim();
  }
  if (rest) chunks.push(rest);
  return chunks;
}

function findAudio(obj) {
  if (!obj || typeof obj !== 'object') return null;
  if (typeof obj.data === 'string' && typeof obj.mime_type === 'string' && obj.mime_type.startsWith('audio/')) return obj;
  if (typeof obj.data === 'string' && obj.type === 'audio') return obj;
  if (Array.isArray(obj)) {
    for (const x of obj) {
      const a = findAudio(x);
      if (a) return a;
    }
  } else {
    for (const k of Object.keys(obj)) {
      const a = findAudio(obj[k]);
      if (a) return a;
    }
  }
  return null;
}

function base64ToBytes(s) {
  return new Uint8Array(Buffer.from(s, 'base64'));
}

function pcmWav(pcm, sampleRate = 24000, channels = 1, bits = 16) {
  const dataLen = pcm.length;
  const out = Buffer.alloc(44 + dataLen);
  let o = 0;
  out.write('RIFF', o); o += 4;
  out.writeUInt32LE(36 + dataLen, o); o += 4;
  out.write('WAVE', o); o += 4;
  out.write('fmt ', o); o += 4;
  out.writeUInt32LE(16, o); o += 4;
  out.writeUInt16LE(1, o); o += 2;
  out.writeUInt16LE(channels, o); o += 2;
  out.writeUInt32LE(sampleRate, o); o += 4;
  const byteRate = sampleRate * channels * bits / 8;
  out.writeUInt32LE(byteRate, o); o += 4;
  out.writeUInt16LE(channels * bits / 8, o); o += 2;
  out.writeUInt16LE(bits, o); o += 2;
  out.write('data', o); o += 4;
  out.writeUInt32LE(dataLen, o); o += 4;
  Buffer.from(pcm).copy(out, o);
  return out;
}

function processPcm(input, speed = 1, volume = 1) {
  const src = Buffer.from(input);
  const rate = Math.max(0.7, Math.min(1.3, Number(speed) || 1));
  const volumeNumber = Number(volume);
  const gain = Math.max(0, Math.min(1, Number.isFinite(volumeNumber) ? volumeNumber : 1));
  const sampleCount = Math.floor(src.length / 2);
  const outCount = Math.max(1, Math.floor(sampleCount / rate));
  const out = Buffer.alloc(outCount * 2);
  for (let i = 0; i < outCount; i++) {
    const pos = Math.min(sampleCount - 1, Math.floor(i * rate));
    const sample = src.readInt16LE(pos * 2);
    const scaled = Math.max(-32768, Math.min(32767, Math.round(sample * gain)));
    out.writeInt16LE(scaled, i * 2);
  }
  return out;
}

function isRetryableStatus(status) {
  return status === 408 || status === 429 || status === 500 || status === 502 || status === 503 || status === 504;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function cleanErrorMessage(status, rawMessage) {
  const message = String(rawMessage || '').trim();
  if (status === 429) return 'Gemini AI Voice limit ရောက်နေပါတယ်။ ခဏစောင့်ပြီး ထပ်စမ်းပါ။ မကြာခဏဖြစ်ရင် Gemini API quota/billing ကို စစ်ပါ။';
  if (status === 401 || status === 403) return 'Gemini API Key / project permission ပြဿနာရှိပါတယ်။ Server-side GEMINI_API_KEY ကို စစ်ပါ။';
  if (status === 400) return message || 'Gemini request မမှန်ကန်ပါ။ Voice / text / style ကို စစ်ပါ။';
  return message || `Gemini API error ${status}`;
}

async function generateChunk(apiKey, text, voice, style, language) {
  const isEnglish = language === 'en';
  const languageName = isEnglish ? 'English' : 'Burmese (Myanmar)';
  const speechLanguage = isEnglish ? 'en-US' : 'my';
  const prompt = `Synthesize speech only. Do not explain anything. Language: ${languageName}. Read the transcript exactly in ${languageName}. Voice direction: ${style || 'Speak naturally, clearly and warmly.'}\nSpoken transcript:\n${text}`;
  let lastError = null;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const r = await fetch('https://generativelanguage.googleapis.com/v1beta/interactions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': apiKey,
          'Api-Revision': '2026-05-20'
        },
        body: JSON.stringify({
          model: MODEL,
          input: prompt,
          response_format: { type: 'audio' },
          generation_config: {
            speech_config: [{
              voice: voice || 'Kore',
              language: speechLanguage
            }]
          }
        })
      });

      const data = await r.json().catch(() => ({}));
      if (r.ok) {
        const audio = findAudio(data);
        if (!audio) throw new Error('Gemini returned no audio data');
        return base64ToBytes(audio.data);
      }

      const rawMessage = data?.error?.message || `Gemini API error ${r.status}`;
      const error = new Error(cleanErrorMessage(r.status, rawMessage));
      error.status = r.status;
      error.rawMessage = rawMessage;
      lastError = error;
      if (!isRetryableStatus(r.status) || attempt === MAX_RETRIES) throw error;
      await sleep(1000 * attempt);
    } catch (e) {
      lastError = e;
      if (attempt === MAX_RETRIES || (e?.status && !isRetryableStatus(e.status))) throw e;
      await sleep(1000 * attempt);
    }
  }
  throw lastError || new Error('Gemini TTS generation failed');
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  try {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) return res.status(500).json({ error: 'GEMINI_API_KEY is not configured on the server.' });

    const { text, voice, style, language, speed, volume } = req.body || {};
    if (!text || typeof text !== 'string') return res.status(400).json({ error: 'Text is required.' });

    // There is deliberately no user-facing total-character limit here.
    // The browser batches long text into safe requests so each Vercel response stays small.
    const selectedLanguage = language === 'en' ? 'en' : 'my';
    const chunks = chunkText(text);
    const audioChunks = [];
    for (const chunk of chunks) {
      audioChunks.push(await generateChunk(apiKey, chunk, voice, style, selectedLanguage));
    }

    const rawPcm = Buffer.concat(audioChunks.map(b => Buffer.from(b)));
    const processedPcm = processPcm(rawPcm, speed, volume);
    const wav = pcmWav(processedPcm);
    const volumeNumber = Number(volume);
    const normalizedVolume = Math.max(0, Math.min(1, Number.isFinite(volumeNumber) ? volumeNumber : 1));

    return res.status(200).json({
      mime: 'audio/wav',
      filename: 'gemini-ai-voice.wav',
      audio: wav.toString('base64'),
      chunks: chunks.length,
      model: MODEL,
      provider: 'gemini',
      language: selectedLanguage === 'en' ? 'en-US' : 'my',
      speed: Math.max(0.7, Math.min(1.3, Number(speed) || 1)),
      volume: normalizedVolume,
      fallbackAvailable: true
    });
  } catch (e) {
    const status = Number(e?.status) || 500;
    const clientStatus = status === 429 ? 429 : (status >= 500 ? 503 : status === 400 ? 400 : 500);
    return res.status(clientStatus).json({
      error: e?.message || 'TTS generation failed.',
      provider: 'gemini',
      fallback: 'browser',
      retryable: clientStatus === 429 || clientStatus === 503
    });
  }
}
