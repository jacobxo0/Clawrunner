#!/usr/bin/env node
// Builds openclaw.json from template by substituting ${VAR} with env vars.
const fs = require('fs');
const path = require('path');

const root = process.argv[2] || process.cwd();
const src = path.join(root, 'openclaw.railway.example.json');
const dst = path.join(root, 'openclaw.json');

const template = fs.readFileSync(src, 'utf8');

// Replace ${VAR} with env value (empty string if not set)
const substituted = template.replace(/\$\{([^}]+)\}/g, function(match, name) {
  const v = process.env[name];
  return v !== undefined ? v : '';
});

let cfg = JSON.parse(substituted);

// Handle TELEGRAM_GROUP_ALLOW_FROM as JSON array
const telegramAllow = process.env.TELEGRAM_GROUP_ALLOW_FROM || '[]';
let arr;
try {
  const parsed = JSON.parse(telegramAllow);
  arr = Array.isArray(parsed) ? parsed : [parsed];
} catch (_) {
  arr = [telegramAllow];
}
arr = arr.map(String);
if (cfg.channels && cfg.channels.telegram) {
  cfg.channels.telegram.groupAllowFrom = arr;
  cfg.channels.telegram.allowFrom = arr;
}

fs.writeFileSync(dst, JSON.stringify(cfg, null, 2));

// Debug output
const written = fs.readFileSync(dst, 'utf8');
const ki = written.indexOf('"apiKey"');
console.log('[build-config] apiKey snippet:', ki >= 0 ? written.substring(ki, ki + 30) : 'not found');
console.log('[build-config] primary:', cfg.agents && cfg.agents.defaults && cfg.agents.defaults.model && cfg.agents.defaults.model.primary);
