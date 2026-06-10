FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copy runtime and app
COPY ai-factory-runtime/ /app/ai-factory-runtime/
COPY AgentDevOS/ /app/AgentDevOS/

# Install Python deps
RUN pip install --no-cache-dir \
    -e /app/ai-factory-runtime \
    -e /app/AgentDevOS
