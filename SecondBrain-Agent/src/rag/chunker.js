function chunk(text, size = 1000, overlap = 100) { if (!Number.isInteger(size) || size < 1 || size > 10_000 || !Number.isInteger(overlap) || overlap < 0 || overlap >= size) throw new Error('Invalid chunk settings'); const value = String(text); if (value.length > 5_000_000) throw new Error('Document is too large'); const result = []; for (let i = 0; i < value.length; i += size - overlap) result.push(value.slice(i, i + size)); return result; }
module.exports = { chunk };

