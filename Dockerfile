FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install static docker CLI so container can communicate with Docker host
RUN curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-24.0.7.tgz | \
    tar -xzC /tmp && \
    mv /tmp/docker/docker /usr/local/bin/docker && \
    rm -rf /tmp/docker

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "google-genai>=2.24.0" \
    "fastapi>=0.141.1" \
    "uvicorn>=0.53.0" \
    "langgraph>=1.2.11" \
    "pydantic>=2.13.5" \
    "docker>=7.2.0" \
    "httpx>=0.28.1" \
    "pytest>=8.0.0" \
    "mcp" \
    "python-dotenv" || true

COPY . .

EXPOSE 8000

CMD ["uvicorn", "control_plane.main:app", "--host", "0.0.0.0", "--port", "8000"]
