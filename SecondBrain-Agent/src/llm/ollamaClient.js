function endpoint() {
  const url = new URL(process.env.OLLAMA_URL || 'http://127.0.0.1:11434');
  const hostname = url.hostname.replace(/^\[|\]$/g, '').toLowerCase();
  if (!['http:', 'https:'].includes(url.protocol) || !['127.0.0.1', 'localhost', '::1'].includes(hostname)) throw new Error('OLLAMA_URL must use an allowed local host');
  return new URL('/api/generate', url);
}
function buildPrompt(prompt) {
  const history = Array.isArray(prompt.history) ? prompt.history : [];
  const turns = history
    .filter((entry) => ['user', 'assistant'].includes(entry?.role) && typeof entry.content === 'string')
    .map((entry) => `${entry.role === 'user' ? 'User' : 'Assistant'}: ${entry.content}`);
  return [prompt.system, ...turns, `User: ${prompt.user}`].join('\n\n');
}
async function complete(prompt) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch(endpoint(), { method: 'POST', signal: controller.signal, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ model: process.env.OLLAMA_MODEL || 'llama3.2', prompt: buildPrompt(prompt), stream: false }) });
    if (!response.ok) throw new Error(`Ollama request failed (${response.status})`);
    return String((await response.json()).response || '').slice(0, 50_000);
  } finally { clearTimeout(timeout); }
}
module.exports = { buildPrompt, complete, endpoint };

