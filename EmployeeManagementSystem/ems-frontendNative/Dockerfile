FROM node:20-alpine

# Expo requires bash and a few other dependencies
RUN apk add --no-cache bash libc6-compat

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (use legacy-peer-deps to avoid conflicts if any)
RUN npm install --legacy-peer-deps

# Copy the rest of the native app files
COPY . .

# Expose Metro bundler port
EXPOSE 8081

# Start Expo dev server
CMD ["npx", "expo", "start"]
