const { spawn } = require('node:child_process');
const ALLOWED = new Map();
function run(command, args = []) {
  if (!process.env.ENABLE_TERMINAL || !ALLOWED.has(command)) return Promise.reject(new Error('Terminal tool is disabled'));
  if (!Array.isArray(args) || args.some((arg) => typeof arg !== 'string')) return Promise.reject(new Error('Invalid arguments'));
  return new Promise((resolve, reject) => {
    const child = spawn(ALLOWED.get(command), args, { shell: false, windowsHide: true, timeout: 10_000 });
    let output = '';
    child.stdout.on('data', (chunk) => { output = (output + chunk).slice(0, 100_000); });
    child.on('error', reject);
    child.on('close', (code) => code === 0 ? resolve(output) : reject(new Error(`Command failed (${code})`)));
  });
}
module.exports = { run };

