const fs = require('node:fs/promises');
const path = require('node:path');
const { assertSafeDirectory, safePath } = require('./fileSystem');
module.exports = { name: 'notes', description: 'Write a note inside the local vault', async execute(input) { const title = String(input?.title || 'note').replace(/[^\w.-]/g, '_').slice(0, 80); const content = String(input?.content || '').slice(0, 100_000); const target = safePath(path.join('notes', `${title}.md`)); await fs.mkdir(path.dirname(target), { recursive: true }); await assertSafeDirectory(path.dirname(target)); await fs.writeFile(target, content, { encoding: 'utf8', flag: 'wx' }); return { path: target }; } };

