const { createPlan } = require('./planner');
const { buildPrompt } = require('../llm/promptBuilder');
const { complete } = require('../llm/modelRouter');
const chatMemory = require('../memory/chatMemory');
const sessions = require('../memory/sessionStore');

async function respond({ message, sessionId = 'default' }) {
  sessions.touch(sessionId);
  const plan = createPlan(message);
  const prompt = buildPrompt(message, chatMemory.get(sessionId));
  const reply = await complete(prompt);
  chatMemory.append(sessionId, { role: 'user', content: message });
  chatMemory.append(sessionId, { role: 'assistant', content: reply });
  return { reply, plan };
}
module.exports = { respond };

