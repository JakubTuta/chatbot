FROM node:22.12.0-slim AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install --legacy-peer-deps && \
    npm cache clean --force

COPY . .

RUN npm run build

FROM node:22.12.0-alpine AS runner

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs

WORKDIR /app

COPY --from=builder --chown=nextjs:nodejs /app/.output ./.output

ENV DOCKER=true \
    NODE_ENV=production

USER nextjs

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]