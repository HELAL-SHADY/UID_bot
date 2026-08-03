# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

COPY dashboard/package.json dashboard/package-lock.json ./dashboard/
RUN cd dashboard && npm install

COPY dashboard ./dashboard
RUN cd dashboard && npm run build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app/dashboard

COPY --from=builder /app/dashboard/package.json ./package.json
COPY --from=builder /app/dashboard/package-lock.json ./package-lock.json
COPY --from=builder /app/dashboard/.next ./.next
COPY --from=builder /app/dashboard/public ./public
COPY --from=builder /app/dashboard/next.config.mjs ./next.config.mjs
COPY --from=builder /app/dashboard/next-env.d.ts ./next-env.d.ts
COPY --from=builder /app/dashboard/app ./app
COPY --from=builder /app/dashboard/components ./components

RUN npm install --production

EXPOSE 3000
CMD ["npm", "run", "start"]
