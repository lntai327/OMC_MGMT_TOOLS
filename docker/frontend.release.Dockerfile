# =============================================================================
# Stage 1: Build React Frontend with Vite & npm
# =============================================================================
FROM node:22-alpine AS builder

WORKDIR /app

# Copy dependency manifests and install packages
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Copy source code and build production bundle
COPY frontend /app
RUN npm run build

# =============================================================================
# Stage 2: Production Nginx Server with HTTPS & SSL
# =============================================================================
FROM nginx:alpine

# Copy custom Nginx configuration
COPY docker/nginx.release.conf /etc/nginx/conf.d/default.conf

# Copy SSL certificates
COPY storage/certs/cert.pem /etc/nginx/certs/cert.pem
COPY storage/certs/key.pem /etc/nginx/certs/key.pem

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]

