const router = require('express').Router();
const { listTools } = require('../../agent/toolRegistry');
router.get('/', (_req, res) => res.json({ tools: listTools() }));
module.exports = router;

