# Build stage - use slim for build tools / Etap budowania - używamy slim dla narzędzi budowania
FROM node:22.12.0-slim AS builder

# Set working directory / Ustawienie katalogu roboczego
WORKDIR /app

# Copy package files first for better layer caching / Kopiowanie plików package jako pierwsze dla lepszego cache warstw
COPY package*.json ./

# Install all dependencies including dev dependencies / Instalacja wszystkich zależności włącznie z dev
RUN npm install --legacy-peer-deps && \
    npm cache clean --force

# Copy source code / Kopiowanie kodu źródłowego
COPY . .

# Build the application / Budowanie aplikacji
RUN npm run build

# Production stage - use alpine for smaller size / Etap produkcyjny - używamy alpine dla mniejszego rozmiaru
FROM node:22.12.0-alpine AS runner

# Create non-root user for security / Tworzenie użytkownika non-root dla bezpieczeństwa
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 -G nodejs

# Set working directory / Ustawienie katalogu roboczego
WORKDIR /app

# Copy built application with proper ownership / Kopiowanie zbudowanej aplikacji z właściwymi uprawnieniami
COPY --from=builder --chown=nextjs:nodejs /app/.output ./.output

# Set environment variable / Ustawienie zmiennej środowiskowej
ENV DOCKER=true \
    NODE_ENV=production

# Switch to non-root user / Przełączenie na użytkownika non-root
USER nextjs

# Expose port / Udostępnienie portu
EXPOSE 3000

# Run the application / uruch aplikacji
CMD ["node", ".output/server/index.mjs"]