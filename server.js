import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';
import multer from 'multer';
import ffmpegPath from 'ffmpeg-static';
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import ttsHandler from './api/tts.js';

const app = express();
const port = process.env.PORT || 8080;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 100 * 1024 * 1024 } });

app.use(express.json({ limit: '1mb' }));
app.use(express.static(__dirname));

app.options('/api/tts', (req, res) => ttsHandler(req, res));
app.post('/api/tts', (req, res) => ttsHandler(req, res));

async function extractWav(buffer, extension = 'mp4') {
  if (!ffmpegPath) throw new Error('FFmpeg is not available on this server');
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'voice-studio-'));
  const inputPath = path.join(tempDir, `input.${extension}`);
  const outputPath = path.join(tempDir, 'audio.wav');
  fs.writeFileSync(inputPath, buffer);
  try {
    await new Promise((resolve, reject) => {
      const ff = spawn(ffmpegPath, [
        '-hide_banner', '-loglevel', 'error', '-y',
        '-i', inputPath,
        '-vn', '-ac', '1', '-ar', '22050', '-c:a', 'pcm_s16le',
        outputPath
      ]);
      let err = '';
      ff.stderr.on('data', d => { err += d.toString(); });
      ff.on('error', reject);
      ff.on('close', code => code === 0 ? resolve() : reject(new Error(err || `FFmpeg exited with ${code}`)));
    });
    return fs.readFileSync(outputPath);
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

app.post('/api/extract-audio', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'file is required' });
  try {
    const audio = await extractWav(req.file.buffer, 'mp4');
    res.setHeader('Content-Type', 'audio/wav');
    res.setHeader('Content-Disposition', 'attachment; filename="voice-sample.wav"');
    res.send(audio);
  } catch (e) {
    res.status(422).json({ error: `Audio extraction failed: ${e.message}` });
  }
});

// Voice-clone gateway. Set CLONE_BACKEND_URL to a real clone engine endpoint.
// MP4 uploads are converted to mono 22.05 kHz WAV before forwarding.
app.post('/api/clone', upload.any(), async (req, res) => {
  const cloneUrl = process.env.CLONE_BACKEND_URL;
  const incoming = (req.files || []).find(f => ['file', 'sample', 'audio'].includes(f.fieldname)) || req.files?.[0];
  if (!incoming) return res.status(400).json({ error: 'voice sample file is required' });
  if (!cloneUrl) {
    return res.status(503).json({
      error: 'Voice clone backend is not configured',
      hint: 'Set CLONE_BACKEND_URL to your XTTS/OpenVoice/compatible clone API endpoint.'
    });
  }

  try {
    const isMp4 = incoming.mimetype === 'video/mp4' || /\.mp4$/i.test(incoming.originalname || '');
    const bodyBuffer = isMp4 ? await extractWav(incoming.buffer, 'mp4') : incoming.buffer;
    const filename = isMp4 ? 'voice-sample.wav' : (incoming.originalname || 'voice-sample');
    const contentType = isMp4 ? 'audio/wav' : (incoming.mimetype || 'application/octet-stream');

    const form = new FormData();
    form.append('file', new Blob([bodyBuffer], { type: contentType }), filename);
    if (req.body?.text) form.append('text', req.body.text);
    if (req.body?.language) form.append('language', req.body.language);
    if (req.body?.speed) form.append('speed', req.body.speed);

    const upstream = await fetch(cloneUrl, { method: 'POST', body: form });
    const responseType = upstream.headers.get('content-type') || '';
    const data = Buffer.from(await upstream.arrayBuffer());
    res.status(upstream.status);
    if (responseType.includes('application/json')) {
      res.setHeader('Content-Type', 'application/json');
      return res.send(data);
    }
    res.setHeader('Content-Type', responseType || 'audio/wav');
    res.setHeader('Content-Disposition', 'inline; filename="cloned-voice.wav"');
    return res.send(data);
  } catch (e) {
    return res.status(502).json({ error: `Voice clone request failed: ${e.message}` });
  }
});

app.get('/health', (_req, res) => {
  res.status(200).json({
    ok: true,
    service: 'ai-voice-studio',
    mp4Extraction: Boolean(ffmpegPath),
    cloneGateway: Boolean(process.env.CLONE_BACKEND_URL)
  });
});

app.get(/.*/, (_req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log(`AI Voice Studio listening on ${port}`);
});
