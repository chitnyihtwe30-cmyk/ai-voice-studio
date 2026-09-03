import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';
import ttsHandler from './api/tts.js';

const app = express();
const port = process.env.PORT || 8080;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(express.json({ limit: '1mb' }));
app.use(express.static(__dirname));

app.options('/api/tts', (req, res) => ttsHandler(req, res));
app.post('/api/tts', (req, res) => ttsHandler(req, res));

app.get('/health', (_req, res) => {
  res.status(200).json({ ok: true, service: 'ai-voice-studio' });
});

app.get('*', (_req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log(`AI Voice Studio listening on ${port}`);
});
