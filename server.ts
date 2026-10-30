import express, { Request, Response } from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { runTravelAgent, resumeTravelAgent } from './src/server/travelAgents.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = parseInt(process.env.PORT || '3000', 10);

app.use(cors());
app.use(express.json());

// API Endpoints matching original backend
app.post('/api/travel', async (req: Request, res: Response) => {
  try {
    const { message, thread_id } = req.body || {};
    const userMessage = typeof message === 'string' ? message.trim() : '';

    if (!userMessage) {
      res.status(400).json({
        success: false,
        error: 'Message cannot be empty.',
      });
      return;
    }

    const result = await runTravelAgent(userMessage, thread_id);
    res.json(result);
  } catch (error: any) {
    console.error('Travel planner error:', error);
    res.status(500).json({
      success: false,
      error: error?.message || 'An unexpected error occurred while planning your trip.',
    });
  }
});

app.post('/api/travel/approve', async (req: Request, res: Response) => {
  try {
    const { thread_id, approved, feedback } = req.body || {};

    if (!thread_id) {
      res.status(400).json({
        success: false,
        error: 'thread_id is required.',
      });
      return;
    }

    if (!approved && (!feedback || !feedback.trim())) {
      res.status(400).json({
        success: false,
        error: 'Please provide revision feedback when rejecting the draft.',
      });
      return;
    }

    const result = await resumeTravelAgent(thread_id, Boolean(approved), feedback || '');
    res.json(result);
  } catch (error: any) {
    console.error('Travel approval error:', error);
    res.status(500).json({
      success: false,
      error: error?.message || 'Failed to process travel plan approval.',
    });
  }
});

app.get('/health', (_req: Request, res: Response) => {
  res.json({
    status: 'ok',
    message: 'TripMate AI API is running',
    features: ['supervisor_agent', 'input_guardrail', 'human_in_the_loop', 'specialist_agents'],
  });
});

async function startServer() {
  const isDev = process.env.NODE_ENV !== 'production';

  if (isDev) {
    const { createServer: createViteServer } = await import('vite');
    const vite = await createViteServer({
      server: { middlewareMode: true, host: '0.0.0.0', port: PORT },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.resolve(__dirname, 'dist');
    app.use(express.static(distPath));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 TripMate AI server running at http://0.0.0.0:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
