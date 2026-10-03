function errorHandler(error, req, res, _next) {
  const payloadTooLarge = error?.type === 'entity.too.large';
  const invalidJson = error?.type === 'entity.parse.failed';
  const status = payloadTooLarge ? 413 : invalidJson ? 400 : 500;
  const code = payloadTooLarge ? 'PAYLOAD_TOO_LARGE' : invalidJson ? 'INVALID_JSON' : 'INTERNAL_ERROR';
  const message = payloadTooLarge ? 'Request body is too large' : invalidJson ? 'Request body contains invalid JSON' : 'Unexpected server error';
  res.status(status).json({
    error: { code, message },
    requestId: req.requestId,
  });
}
module.exports = { errorHandler };

