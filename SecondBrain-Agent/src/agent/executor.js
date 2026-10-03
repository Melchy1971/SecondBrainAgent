const { getTool } = require('./toolRegistry');
async function executeTool(name, input) {
  const tool = getTool(name);
  if (!tool) throw new Error('Tool is not allowed');
  return tool.execute(input);
}
module.exports = { executeTool };

