const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createApp, loadEnvironment } = require('../src/server/app');
const claude = require('../src/llm/claudeClient');
const ollama = require('../src/llm/ollamaClient');
const { safePath } = require('../src/tools/fileSystem');
const terminal = require('../src/tools/terminal');

async function withServer(run) { const server = createApp().listen(0, '127.0.0.1'); await new Promise((resolve) => server.once('listening', resolve)); try { await run(`http://127.0.0.1:${server.address().port}`); } finally { await new Promise((resolve) => server.close(resolve)); } }
test('health is stable', () => withServer(async (base) => { const response = await fetch(`${base}/health`); assert.equal(response.status, 200); assert.deepEqual(await response.json(), { status: 'ok' }); }));
test('chat validates input', () => withServer(async (base) => { const response = await fetch(`${base}/chat`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ message: '' }) }); assert.equal(response.status, 400); }));
test('chat succeeds in mock mode', () => withServer(async (base) => { const response = await fetch(`${base}/chat`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ message: 'hello', sessionId: 'test-chat' }) }); assert.equal(response.status, 200); assert.equal((await response.json()).reply, 'Mock response: hello'); }));
test('chat rejects oversized messages', () => withServer(async (base) => { const response = await fetch(`${base}/chat`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ message: 'x'.repeat(10_001) }) }); assert.equal(response.status, 400); }));
test('invalid JSON returns a stable 400 error', () => withServer(async (base) => { const response = await fetch(`${base}/chat`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{"message":' }); const body = await response.json(); assert.equal(response.status, 400); assert.equal(body.error.code, 'INVALID_JSON'); assert.ok(body.requestId); }));
test('unknown routes return 404', () => withServer(async (base) => { assert.equal((await fetch(`${base}/missing`)).status, 404); }));
test('tool list exposes metadata only', () => withServer(async (base) => { const data = await (await fetch(`${base}/tools`)).json(); assert.ok(data.tools.length); assert.ok(data.tools.every((tool) => !('execute' in tool))); }));
test('filesystem blocks traversal', () => assert.throws(() => safePath('../../outside'), /escapes/));
test('terminal is disabled', async () => assert.rejects(terminal.run('node', ['--version']), /disabled/));
test('optional env files load without overriding existing variables', () => { const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'secondbrain-env-')); const envPath = path.join(directory, '.env'); fs.writeFileSync(envPath, 'SECOND_BRAIN_TEST=from-file\nSECOND_BRAIN_KEEP=file-value\n'); process.env.SECOND_BRAIN_KEEP = 'existing'; try { loadEnvironment(envPath); assert.equal(process.env.SECOND_BRAIN_TEST, 'from-file'); assert.equal(process.env.SECOND_BRAIN_KEEP, 'existing'); } finally { delete process.env.SECOND_BRAIN_TEST; delete process.env.SECOND_BRAIN_KEEP; fs.rmSync(directory, { recursive: true, force: true }); } });
test('provider prompts include valid history', () => { const prompt = { system: 'system', history: [{ role: 'user', content: 'first' }, { role: 'assistant', content: 'second' }, { role: 'tool', content: 'ignored' }], user: 'third' }; assert.deepEqual(claude.buildMessages(prompt), [{ role: 'user', content: 'first' }, { role: 'assistant', content: 'second' }, { role: 'user', content: 'third' }]); assert.match(ollama.buildPrompt(prompt), /User: first[\s\S]*Assistant: second[\s\S]*User: third/); assert.doesNotMatch(ollama.buildPrompt(prompt), /ignored/); });
test('Ollama accepts the IPv6 loopback hostname', () => { const previous = process.env.OLLAMA_URL; process.env.OLLAMA_URL = 'http://[::1]:11434'; try { assert.equal(ollama.endpoint().hostname, '[::1]'); } finally { if (previous === undefined) delete process.env.OLLAMA_URL; else process.env.OLLAMA_URL = previous; } });

