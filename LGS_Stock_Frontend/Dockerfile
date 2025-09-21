# Base image for both dev and build
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./

# Development stage: Installs all dependencies and runs the dev server
FROM base AS development-stage
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"] # The --host flag is now managed by vite.config.js

# Build stage: Installs only production dependencies and builds the app
FROM base AS build-stage
RUN npm install
COPY . .
RUN npm run build
# Production stage: Serves the built static files with Nginx
FROM nginx:stable-alpine AS production-stage

# Copy the built Vue app from the build-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy our custom Nginx configuration that includes the reverse proxy
COPY ./LGS_Stock_Frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
