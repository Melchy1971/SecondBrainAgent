function buildMessages(prompt) {
  const history = Array.isArray(prompt.history) ? prompt.history : [];
  const messages = history
    .filter((entry) => ['user', 'assistant'].includes(entry?.role) && typeof entry.content === 'string')
    .map(({ role, content }) => ({ role, content }));
  messages.push({ role: 'user', content: prompt.user });
  return messages;
}

async function complete(prompt) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error('Claude is not configured');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', { method: 'POST', signal: controller.signal, headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' }, body: JSON.stringify({ model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-5', max_tokens: 1024, system: prompt.system, messages: buildMessages(prompt) }) });
    if (!response.ok) throw new Error(`Claude request failed (${response.status})`);
    const data = await response.json();
    return String(data.content?.[0]?.text || '').slice(0, 50_000);
  } finally { clearTimeout(timeout); }
}
module.exports = { buildMessages, complete };

