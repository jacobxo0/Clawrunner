# Railway: byg med Docker i stedet for Railpack (undgår "Error creating build plan with Railpack").
# Node 20, npm install, kør railway-start.sh.

FROM node:20-bookworm-slim

# npm install kan kalde git (fx ved openclaw eller dependencies fra git)
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (better layer cache)
COPY package.json ./
RUN npm install --omit=dev

# Rest of app (config template, scripts, workspace skeleton)
COPY . .

# Railway sets PORT; start script builds openclaw.json from env and runs gateway
ENV NODE_ENV=production
EXPOSE 18789
CMD ["bash", "scripts/railway-start.sh"]
