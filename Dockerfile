# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies and UV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && curl -Ls https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install Python dependencies using UV
RUN uv pip install --upgrade pip \
    && uv pip install .

# Clean up build dependencies (optional, for smaller image)
RUN apt-get purge -y build-essential curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Set the default command to your CLI
ENTRYPOINT ["poke"]
