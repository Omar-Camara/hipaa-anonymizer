# Docker Setup Guide

This guide explains how to build and run the HIPAA Anonymizer API using Docker.

## Prerequisites

- Docker installed (version 20.10+)
- Docker Compose installed (version 2.0+)

## Quick Start

### Using Docker Compose (Recommended for Development)

1. **Build and start the container:**

   ```bash
   docker compose up --build
   ```

2. **Access the API:**

   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

3. **Stop the container:**
   ```bash
   docker compose down
   ```

### Using Docker Directly

1. **Build the image:**

   ```bash
   docker build -t hipaa-anonymizer:latest .
   ```

2. **Run the container:**

   ```bash
   docker run -d \
     --name hipaa-anonymizer \
     -p 8000:8000 \
     hipaa-anonymizer:latest
   ```

3. **View logs:**

   ```bash
   docker logs -f hipaa-anonymizer
   ```

4. **Stop the container:**
   ```bash
   docker stop hipaa-anonymizer
   docker rm hipaa-anonymizer
   ```

## Production Deployment

### Using Production Dockerfile

For production, use the optimized production Dockerfile:

```bash
# Build production image
docker build -f Dockerfile.prod -t hipaa-anonymizer:prod .

# Run with production settings
docker run -d \
  --name hipaa-anonymizer-prod \
  -p 8000:8000 \
  --restart unless-stopped \
  hipaa-anonymizer:prod
```

**Production features:**

- Multi-stage build (smaller image size)
- Gunicorn with multiple workers
- Optimized for performance
- Non-root user for security

## Configuration

### Environment Variables

You can pass environment variables to the container:

```bash
docker run -d \
  --name hipaa-anonymizer \
  -p 8000:8000 \
  -e HF_TOKEN=your_token_here \
  hipaa-anonymizer:latest
```

Or use a `.env` file with docker compose:

```yaml
# docker-compose.yml
services:
  api:
    environment:
      - HF_TOKEN=${HF_TOKEN}
```

Create a `.env` file:

```
HF_TOKEN=your_token_here
```

### Volume Mounts

Mount local directories for models or data:

```bash
docker run -d \
  --name hipaa-anonymizer \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models:ro \
  -v $(pwd)/data:/app/data:ro \
  hipaa-anonymizer:latest
```

## Docker Compose Options

### Development Mode (with hot reload)

Create `docker-compose.dev.yml`:

```yaml
version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./src:/app/src # Mount source for hot reload
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Run with:

```bash
docker compose -f docker-compose.dev.yml up
```

### Production Mode

```bash
docker compose -f docker-compose.yml up -d
```

## Troubleshooting

### Container won't start

1. **Check logs:**

   ```bash
   docker logs hipaa-anonymizer-api
   ```

2. **Check if port is in use:**

   ```bash
   lsof -i :8000
   ```

3. **Verify image was built correctly:**
   ```bash
   docker images | grep hipaa-anonymizer
   ```

### spaCy model not found

The Dockerfile automatically downloads `en_core_web_sm`. If it fails:

1. **Check build logs:**

   ```bash
   docker build -t hipaa-anonymizer:latest . 2>&1 | grep -i spacy
   ```

2. **Manually install in container:**
   ```bash
   docker exec -it hipaa-anonymizer-api python -m spacy download en_core_web_sm
   ```

### Out of memory

If you're running Tier 3 (SLM models), you may need more memory:

```yaml
# docker-compose.yml (or docker compose)
services:
  api:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

### Health check failing

The health check runs every 30 seconds. If it's failing:

1. **Check if API is responding:**

   ```bash
   curl http://localhost:8000/health
   ```

2. **Check container status:**
   ```bash
   docker ps -a | grep hipaa-anonymizer
   ```

## Building for Different Platforms

### Build for ARM64 (Apple Silicon, Raspberry Pi)

```bash
docker buildx build --platform linux/arm64 -t hipaa-anonymizer:arm64 .
```

### Build for AMD64 (Intel/AMD)

```bash
docker buildx build --platform linux/amd64 -t hipaa-anonymizer:amd64 .
```

## Image Size Optimization

The production Dockerfile uses multi-stage builds to reduce image size:

- **Development image**: ~2-3 GB (includes build tools)
- **Production image**: ~1-1.5 GB (runtime only)

## Security Best Practices

1. **Non-root user**: The container runs as `appuser` (UID 1000)
2. **Minimal base image**: Uses `python:3.11-slim`
3. **No secrets in image**: Use environment variables or secrets management
4. **Read-only volumes**: Mount data as read-only when possible
5. **Health checks**: Automatic container health monitoring

## Next Steps

- [ ] Add authentication middleware
- [ ] Set up reverse proxy (nginx)
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and logging
- [ ] Deploy to cloud platform (AWS, GCP, Azure)

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
