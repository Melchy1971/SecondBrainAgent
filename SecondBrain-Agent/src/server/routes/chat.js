const router = require('express').Router();
const { z } = require('zod');
const { respond } = require('../../agent/jarvisAgent');

const schema = z.object({
  message: z.string().trim().min(1).max(10_000),
  sessionId: z.string().trim().min(1).max(128).regex(/^[\w.-]+$/).optional(),
}).strict();

router.post('/', async (req, res, next) => {
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: { code: 'INVALID_INPUT', message: 'Invalid chat request' }, requestId: req.requestId });
  try {
    const result = await respond(parsed.data);
    return res.json(result);
  } catch (error) {
    return next(error);
  }
});
module.exports = router;

