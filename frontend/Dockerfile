FROM node:20

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install the exact dependency versions in package-lock.json
RUN npm ci && \
    sha256sum package-lock.json | cut -d ' ' -f 1 > node_modules/.package-lock.sha256

# Copy the rest of the application code
COPY . .

# Expose the port the React app will run on
EXPOSE 3000

CMD ["sh", "./docker-entrypoint.dev.sh"]
