import express from 'express';
import { fileURLToPath } from 'url';
import path from 'path';

const app = express();
const port = process.env.PORT || 8080;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(express.static(__dirname));
app.get('/health', (_req, res) => res.json({ ok: true, service: 'ai-voice-studio', mode: 'local-only' }));
app.get(/.*/, (_req, res) => res.sendFile(path.join(__dirname, 'index.html')));

app.listen(port, '0.0.0.0', () => console.log(`AI Voice Studio local server listening on ${port}`));
