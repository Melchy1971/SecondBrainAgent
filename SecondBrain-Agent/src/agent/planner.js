function createPlan(message) {
  return [{ type: 'respond', input: String(message).slice(0, 10_000) }];
}
module.exports = { createPlan };

