const vectors = [];
function add(item) { vectors.push(Object.freeze({ ...item })); }
function all() { return [...vectors]; }
module.exports = { add, all };

