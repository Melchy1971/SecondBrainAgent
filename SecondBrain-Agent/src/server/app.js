const crypto = require('node:crypto');
const path = require('node:path');
const dotenv = require('dotenv');

function loadEnvironment(envPath = path.join(__dirname, '..', '..', '.env')) {
  return dotenv.config({ path: envPath, override: false, quiet: true });
}

loadEnvironment();

const express = require('express');
const health = require('./routes/health');
const chat = require('./routes/chat');
const tools = require('./routes/tools');
const { errorHandler } = require('./middleware/errorHandler');

function parsePort(value) {
  const port = Number(value ?? 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('PORT must be an integer from 1 to 65535');
  return port;
}

function createApp() {
  const app = express();
  app.disable('x-powered-by');
  app.use((req, res, next) => {
    req.requestId = req.get('x-request-id')?.slice(0, 128) || crypto.randomUUID();
    res.set('x-request-id', req.requestId);
    next();
  });
  app.use(express.json({ limit: '1mb' }));
  app.use('/health', health);
  app.use('/chat', chat);
  app.use('/tools', tools);
  app.use((req, res) => res.status(404).json({ error: { code: 'NOT_FOUND', message: 'Route not found' }, requestId: req.requestId }));
  app.use(errorHandler);
  return app;
}

function startServer() {
  const port = parsePort(process.env.PORT);
  const host = process.env.HOST || '127.0.0.1';
  return createApp().listen(port, host, () => console.log(`SecondBrain Agent listening on http://${host}:${port}`));
}

if (require.main === module) startServer();
module.exports = { createApp, loadEnvironment, parsePort, startServer };

