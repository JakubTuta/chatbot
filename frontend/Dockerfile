# Stage 1: Build Stage
FROM node:18 AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production Stage
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy built assets from the build stage
COPY --from=builder /app/.output ./.output

# Set the environment variable
ENV DOCKER "true"

# Expose the port
EXPOSE 3000

# Start the Nuxt app
CMD ["node", ".output/server/index.mjs"]
