function embed(text) { const value = String(text); let hash = 2166136261; for (const char of value) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619); return [((hash >>> 0) / 0xffffffff)]; }
module.exports = { embed };

