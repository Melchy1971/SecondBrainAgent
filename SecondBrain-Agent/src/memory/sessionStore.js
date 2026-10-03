const sessions = new Map();
function touch(id) { sessions.set(id, { updatedAt: new Date().toISOString() }); return sessions.get(id); }
module.exports = { touch };

