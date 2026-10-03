const store = require('../memory/documentStore');
module.exports = { name: 'knowledgeSearch', description: 'Search indexed local knowledge', async execute(input) { return store.search(String(input?.query || '').slice(0, 500)); } };

