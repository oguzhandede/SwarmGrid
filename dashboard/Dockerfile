FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

# Create public folder if it doesn't exist
RUN mkdir -p public

# Copy built assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Try to copy public folder if it exists
COPY --from=builder /app/public ./public

EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
