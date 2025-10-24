# -----------------------------------------------------------------------------
# Stage 1: Base - Install all dependencies
# -----------------------------------------------------------------------------
# This stage installs both production and development dependencies.
# It's used as a foundation for both the 'test' and 'builder' stages.
FROM node:20-alpine as base
WORKDIR /app
COPY package*.json ./
RUN npm install

# -----------------------------------------------------------------------------
# Stage 2: Test - Run frontend tests
# -----------------------------------------------------------------------------
# This stage copies the source code and runs the test suite.
# The `deploy.sh` script will target this stage to verify code quality.
FROM base as test
WORKDIR /app
COPY . .
# This command assumes your tests are configured to run via `npm test`.
# If the tests fail, the Docker build will stop here.
RUN npm test

# -----------------------------------------------------------------------------
# Stage 3: Builder - Create the production build
# -----------------------------------------------------------------------------
FROM base as builder
WORKDIR /app
COPY . .
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 4: Production - Serve the built assets with Nginx
# -----------------------------------------------------------------------------
FROM nginx:1.25-alpine as production
COPY --from=builder /app/dist /usr/share/nginx/html
# You can add a custom nginx.conf here if needed
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
