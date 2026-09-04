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

app.post('/api/extract-audio', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'file is required' });

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'voice-studio-'));
  const inputPath = path.join(tempDir, 'input');
  const outputPath = path.join(tempDir, 'audio.wav');
  fs.writeFileSync(inputPath, req.file.buffer);

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

    const audio = fs.readFileSync(outputPath);
    res.setHeader('Content-Type', 'audio/wav');
    res.setHeader('Content-Disposition', 'attachment; filename="voice-sample.wav"');
    res.send(audio);
  } catch (e) {
    res.status(422).json({ error: `Audio extraction failed: ${e.message}` });
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
});

app.get('/health', (_req, res) => {
  res.status(200).json({ ok: true, service: 'ai-voice-studio', mp4Extraction: Boolean(ffmpegPath) });
});

app.get(/.*/, (_req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log(`AI Voice Studio listening on ${port}`);
});
