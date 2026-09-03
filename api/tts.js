const MODEL = 'gemini-3.1-flash-tts-preview';
const MAX_CHARS = 2600;

function chunkText(text) {
  const chunks = [];
  let rest = text.trim();
  while (rest.length > MAX_CHARS) {
    let cut = rest.lastIndexOf('။', MAX_CHARS);
    if (cut < MAX_CHARS * 0.55) cut = rest.lastIndexOf(' ', MAX_CHARS);
    if (cut < MAX_CHARS * 0.55) cut = MAX_CHARS;
    chunks.push(rest.slice(0, cut + (rest[cut] === '။' ? 1 : 0)).trim());
    rest = rest.slice(cut + (rest[cut] === '။' ? 1 : 0)).trim();
  }
  if (rest) chunks.push(rest);
  return chunks;
}

function findAudio(obj) {
  if (!obj || typeof obj !== 'object') return null;
  if (typeof obj.data === 'string' && typeof obj.mime_type === 'string' && obj.mime_type.startsWith('audio/')) return obj;
  if (typeof obj.data === 'string' && obj.type === 'audio') return obj;
  if (Array.isArray(obj)) {
    for (const x of obj) { const a = findAudio(x); if (a) return a; }
  } else {
    for (const k of Object.keys(obj)) { const a = findAudio(obj[k]); if (a) return a; }
  }
  return null;
}

function base64ToBytes(s) {
  const bin = Buffer.from(s, 'base64');
  return new Uint8Array(bin);
}

function pcmWav(chunks, sampleRate = 24000, channels = 1, bits = 16) {
  const dataLen = chunks.reduce((n, b) => n + b.length, 0);
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
  for (const b of chunks) { Buffer.from(b).copy(out, o); o += b.length; }
  return out;
}

async function generateChunk(apiKey, text, voice, style) {
  const prompt = `Synthesize speech only. Do not explain anything. Language: Burmese (Myanmar). Voice direction: ${style || 'Speak naturally, clearly and warmly.'}\nSpoken transcript:\n${text}`;
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
      generation_config: { speech_config: [{ voice: voice || 'Kore' }] }
    })
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || `Gemini API error ${r.status}`);
  const audio = findAudio(data);
  if (!audio) throw new Error('Gemini returned no audio data');
  return base64ToBytes(audio.data);
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
    const { text, voice, style } = req.body || {};
    if (!text || typeof text !== 'string') return res.status(400).json({ error: 'Text is required.' });
    if (text.length > 5000) return res.status(400).json({ error: 'Maximum 5,000 characters.' });
    const chunks = chunkText(text);
    const audioChunks = [];
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        audioChunks.length = 0;
        for (const chunk of chunks) audioChunks.push(await generateChunk(apiKey, chunk, voice, style));
        break;
      } catch (e) {
        if (attempt === 1) throw e;
      }
    }
    const wav = pcmWav(audioChunks);
    return res.status(200).json({
      mime: 'audio/wav',
      filename: 'gemini-burmese-voice.wav',
      audio: wav.toString('base64'),
      chunks: chunks.length,
      model: MODEL
    });
  } catch (e) {
    return res.status(500).json({ error: e?.message || 'TTS generation failed.' });
  }
}
