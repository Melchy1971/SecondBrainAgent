const webSearch = require('../tools/webSearch');
const notes = require('../tools/notes');
const knowledgeSearch = require('../tools/knowledgeSearch');
const registry = new Map([webSearch, notes, knowledgeSearch].map((tool) => [tool.name, tool]));
function getTool(name) { return registry.get(name); }
function listTools() { return [...registry.values()].map(({ name, description }) => ({ name, description })); }
module.exports = { getTool, listTools };

