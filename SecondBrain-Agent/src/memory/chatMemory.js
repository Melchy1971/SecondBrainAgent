const chats = new Map();
function append(id, entry) { const list = chats.get(id) || []; list.push(entry); chats.set(id, list.slice(-40)); }
function get(id) { return [...(chats.get(id) || [])]; }
module.exports = { append, get };

