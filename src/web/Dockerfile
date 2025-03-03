# Stage 1: Build the Angular application
FROM node:19-alpine AS builder
WORKDIR /app

# Set build arguments and environment variables
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

# Copy package files first for better layer caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the source code
COPY . .

# Build the application for production
RUN npm run build:prod

# Stage 2: Serve the application with Nginx
FROM nginx:alpine
WORKDIR /usr/share/nginx/html

# Remove default nginx static files
RUN rm -rf ./*

# Copy the built artifacts from the builder stage
COPY --from=builder /app/dist/interaction-management .

# Copy custom nginx configuration for Angular routing support
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Configure health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]