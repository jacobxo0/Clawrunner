#!/usr/bin/env node
// Builds openclaw.json from template by substituting ${VAR} with env vars.
const fs = require('fs');
const path = require('path');

const root = process.argv[2] || process.cwd();
const src = path.join(root, 'openclaw.railway.example.json');
const dst = path.join(root, 'openclaw.json');

const template = fs.readFileSync(src, 'utf8');

// Erstat ${VAR} med env-værdi (tom streng hvis ikke sat)
const substituted = template.replace(/\$\{([^}]+)\}/g, function(match, name) {
  const v = process.env[name];
  return v !== undefined ? v : '';
});

let cfg = JSON.parse(substituted);

// TELEGRAM_GROUP_ALLOW_FROM: kun override allowFrom/groupAllowFrom hvis ikke-tom.
// Ellers bevares de hardcodede værdier fra templaten (["8572521981"]).
// Vigtigt: en tom TELEGRAM_GROUP_ALLOW_FROM må IKKE tømme allowFrom-listen!
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
  if (arr.length > 0) {
    // Env var er sat — brug den
    cfg.channels.telegram.groupAllowFrom = arr;
    cfg.channels.telegram.allowFrom = arr;
  }
  // Else: behold template-værdier (hardcoded ["8572521981"])
}

fs.writeFileSync(dst, JSON.stringify(cfg, null, 2));

// Debug output
console.log('[build-config] telegram.allowFrom:', JSON.stringify(cfg.channels && cfg.channels.telegram && cfg.channels.telegram.allowFrom));
console.log('[build-config] telegram.botToken sat:', cfg.channels && cfg.channels.telegram && cfg.channels.telegram.botToken ? 'JA' : 'NEJ — TELEGRAM VIRKER IKKE');
console.log('[build-config] model.primary:', cfg.agents && cfg.agents.defaults && cfg.agents.defaults.model && cfg.agents.defaults.model.primary);
console.log('[build-config] GROQ_API_KEY env:', process.env.GROQ_API_KEY ? 'sat (len=' + process.env.GROQ_API_KEY.length + ')' : 'IKKE SAT — 401 ved inference');
