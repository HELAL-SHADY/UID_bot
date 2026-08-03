# ── Build stage ──────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Copy lockfiles first for layer caching
COPY dashboard/package.json dashboard/package-lock.json ./dashboard/
RUN cd dashboard && npm ci

# Copy full dashboard source and build
COPY dashboard ./dashboard
RUN cd dashboard && npm run build

# ── Production stage ──────────────────────────────────────────────────────────
FROM node:20-alpine AS runner
ENV NODE_ENV=production
WORKDIR /app/dashboard

# Copy only what Next.js needs to run in standalone/production
COPY --from=builder /app/dashboard/package.json ./package.json
COPY --from=builder /app/dashboard/package-lock.json ./package-lock.json
COPY --from=builder /app/dashboard/.next ./.next
COPY --from=builder /app/dashboard/next.config.mjs ./next.config.mjs

# Copy public folder if it exists (Next.js expects it)
# Using a wildcard to avoid failure if directory is empty/missing
COPY --from=builder /app/dashboard/public* ./public/

# Install only production dependencies
RUN npm ci --omit=dev

EXPOSE 3000
CMD ["npm", "run", "start"]
