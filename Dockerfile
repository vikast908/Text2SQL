# Multi-stage build: First stage for building frontend
FROM node:20-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build frontend
RUN npm run build

# Second stage: Python backend
FROM python:3.14

# Install Poetry
RUN pip install poetry

# Configure Poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Set the working directory in the container
WORKDIR /app/src

# Copy the Poetry configuration files
COPY pyproject.toml poetry.lock /app/src/

# Install the main dependencies using Poetry
RUN poetry install --only=main

# Copy the rest of the application code
COPY . /app/src/

# Copy built frontend from frontend-builder stage
# Build output goes to ../static relative to /app/frontend, so it's at /app/static
COPY --from=frontend-builder /app/static /app/src/static

# Expose the port the app runs on
EXPOSE 8000

# Create a non-root user and change ownership of the application directory
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app

# Switch to the non-root user
USER appuser

# Specify the command to run the application
CMD ["/usr/local/bin/python", "-m", "src"]