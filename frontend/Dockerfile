# Stage 1: Dependencies ("deps")
# This stage installs npm dependencies and is cached as a separate layer.
# It only rebuilds when package.json or package-lock.json changes.
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm install

# Stage 2: Development ("development-stage")
# This stage uses the pre-installed dependencies from 'deps' and runs the dev server.
FROM deps AS development-stage
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]

# Stage 3: Build ("build-stage")
# This stage uses the pre-installed dependencies from 'deps' and builds the static assets.
FROM deps AS build-stage
COPY . .
RUN npm run build

# Stage 4: Production ("production-stage")
# This is a minimal nginx image that serves the static files built in the previous stage.
FROM nginx:stable-alpine AS production-stage
# Copy the built Vue app from the build-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Copy our custom Nginx configuration that includes the reverse proxy
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
