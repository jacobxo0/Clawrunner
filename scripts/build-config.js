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

// Handle TELEGRAM_GROUP_ALLOW_FROM as JSON array.
// Kun override groupAllowFrom — allowFrom (DM-allowlist) beholdes fra template
// med mindre TELEGRAM_GROUP_ALLOW_FROM eksplicit er sat og ikke-tom.
const telegramAllow = process.env.TELEGRAM_GROUP_ALLOW_FROM || '[]';
let arr;
try {
  const parsed = JSON.parse(telegramAllow);
  arr = Array.isArray(parsed) ? parsed : [parsed];
} catch (_) {
  arr = [telegramAllow];
}
arr = arr.map(String).filter(Boolean);
if (cfg.channels && cfg.channels.telegram) {
  // groupAllowFrom: brug env-array hvis ikke-tom, ellers behold template-værdien
  if (arr.length > 0) {
    cfg.channels.telegram.groupAllowFrom = arr;
    // allowFrom synkroniseres kun hvis env var er sat — ellers bevares template-hardcode
    cfg.channels.telegram.allowFrom = arr;
  }
  // Hvis arr er tom (env var ikke sat): behold template-værdier for begge felter
}
console.log('[build-config] telegram.allowFrom:', JSON.stringify(cfg.channels && cfg.channels.telegram && cfg.channels.telegram.allowFrom));
console.log('[build-config] telegram.groupAllowFrom:', JSON.stringify(cfg.channels && cfg.channels.telegram && cfg.channels.telegram.groupAllowFrom));

fs.writeFileSync(dst, JSON.stringify(cfg, null, 2));

// Debug output
const written = fs.readFileSync(dst, 'utf8');
const ki = written.indexOf('"apiKey"');
console.log('[build-config] apiKey snippet:', ki >= 0 ? written.substring(ki, ki + 30) : 'not found');
console.log('[build-config] primary:', cfg.agents && cfg.agents.defaults && cfg.agents.defaults.model && cfg.agents.defaults.model.primary);
// Groq API key availability (env — LiteLLM reads GROQ_API_KEY automatically)
const groqEnvKey = process.env.GROQ_API_KEY || '';
console.log('[build-config] GROQ_API_KEY env set:', groqEnvKey.length > 0 ? 'YES (len=' + groqEnvKey.length + ')' : 'NO — 401 will occur at inference time');
