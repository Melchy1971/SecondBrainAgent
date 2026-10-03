const store = require('../memory/documentStore');
function retrieve(query) { return store.search(String(query).slice(0, 500)); }
module.exports = { retrieve };

