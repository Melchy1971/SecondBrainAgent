const fs = require('node:fs/promises');
const path = require('node:path');
const ROOT = path.resolve(process.env.SECONDBRAIN_WORKSPACE || path.join(__dirname, '..', '..', 'vault'));
function safePath(candidate) {
  const target = path.resolve(ROOT, candidate);
  const relative = path.relative(ROOT, target);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('Path escapes workspace');
  return target;
}
function assertContained(target) {
  const relative = path.relative(ROOT, target);
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('Path escapes workspace');
  return target;
}
async function safeExistingPath(candidate) {
  return assertContained(await fs.realpath(safePath(candidate)));
}
async function assertSafeDirectory(candidate) {
  return assertContained(await fs.realpath(candidate));
}
async function readText(candidate) { return fs.readFile(await safeExistingPath(candidate), { encoding: 'utf8' }); }
module.exports = { ROOT, assertSafeDirectory, readText, safeExistingPath, safePath };

