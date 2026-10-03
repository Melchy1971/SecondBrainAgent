const documents = [];
function add(document) { documents.push(Object.freeze({ ...document })); }
function search(query) { const needle = query.toLowerCase(); return documents.filter((item) => String(item.text || '').toLowerCase().includes(needle)).slice(0, 20); }
module.exports = { add, search };

