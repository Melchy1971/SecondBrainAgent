const { SYSTEM_PROMPT } = require('../agent/systemPrompt');
function buildPrompt(message, history = []) { return { system: SYSTEM_PROMPT, history: history.slice(-20), user: String(message) }; }
module.exports = { buildPrompt };

