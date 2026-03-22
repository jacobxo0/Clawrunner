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

// Remove Groq provider if GROQ_API_KEY is not set (empty apiKey causes 401)
if (cfg.models && cfg.models.providers && cfg.models.providers.groq) {
  const groqApiKey = cfg.models.providers.groq.apiKey || '';
  if (!groqApiKey) {
    delete cfg.models.providers.groq;
    console.log('[build-config] WARNING: Groq provider removed (GROQ_API_KEY not set) — 401 will occur!');
  }
}

// Remove models section entirely if no providers remain
if (cfg.models && cfg.models.providers && Object.keys(cfg.models.providers).length === 0) {
  delete cfg.models;
  console.log('[build-config] models.providers is empty — removed models section.');
}

fs.writeFileSync(dst, JSON.stringify(cfg, null, 2));

// Debug output
const written = fs.readFileSync(dst, 'utf8');
const ki = written.indexOf('"apiKey"');
console.log('[build-config] apiKey snippet:', ki >= 0 ? written.substring(ki, ki + 30) : 'not found');
console.log('[build-config] primary:', cfg.agents && cfg.agents.defaults && cfg.agents.defaults.model && cfg.agents.defaults.model.primary);
const groqKey = cfg.models && cfg.models.providers && cfg.models.providers.groq && cfg.models.providers.groq.apiKey;
console.log('[build-config] groq.apiKey set:', groqKey && groqKey.length > 0 ? 'YES (len=' + groqKey.length + ')' : 'NO — 401 will occur');
console.log('[build-config] providers present:', cfg.models && cfg.models.providers ? Object.keys(cfg.models.providers).join(', ') : 'none');
