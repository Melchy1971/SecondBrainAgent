const claude = require('./claudeClient');
const ollama = require('./ollamaClient');
async function complete(prompt) {
  const provider = (process.env.LLM_PROVIDER || 'mock').toLowerCase();
  if (provider === 'claude') return claude.complete(prompt);
  if (provider === 'ollama') return ollama.complete(prompt);
  if (provider !== 'mock') throw new Error('Unsupported LLM provider');
  return `Mock response: ${prompt.user}`;
}
module.exports = { complete };

