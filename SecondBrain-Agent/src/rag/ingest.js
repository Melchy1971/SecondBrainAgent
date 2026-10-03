const path = require('node:path');
const { chunk } = require('./chunker');
const ALLOWED = new Set(['.md', '.txt']);
function ingest(name, content) { if (!ALLOWED.has(path.extname(String(name)).toLowerCase())) throw new Error('Unsupported document type'); return chunk(content); }
module.exports = { ingest };

