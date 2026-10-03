module.exports = { name: 'webSearch', description: 'Search the web when a provider is configured', async execute(input) { const query = String(input?.query || '').trim(); if (!query || query.length > 500) throw new Error('Invalid query'); throw new Error('Web search is not configured'); } };

