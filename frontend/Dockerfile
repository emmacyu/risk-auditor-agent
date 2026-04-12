# === Stage 1: Build ===
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source
COPY . .

# Build the Vite application for production
RUN npm run build

# === Stage 2: Serve ===
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy from build stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Overwrite default nginx config with our SPA config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 (mapped externally to 5173)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
