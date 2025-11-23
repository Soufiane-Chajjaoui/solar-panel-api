# 🐳 Docker Setup Guide

## 📋 Prerequisites

- Docker installed (https://www.docker.com/products/docker-desktop)
- Docker Compose installed
- Port 8000 available

## 🚀 Quick Start

### Using the management script:

```bash
# Build and start
./docker-dev.sh build
./docker-dev.sh run

# View logs
./docker-dev.sh logs

# Stop
./docker-dev.sh stop

# Clean up
./docker-dev.sh clean
```

### Using docker-compose directly:

```bash
# Start API
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop
docker-compose down
```

## 📍 Access Points

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

## ⚙️ Configuration

### Development Environment

Copy `.env.example` or `.env.docker` to `.env`:
```bash
cp .env.example .env
# Or for Docker
cp .env.docker .env
```

### Production Build

Build production image with optimizations:
```bash
./docker-dev.sh build-prod
docker run -p 8000:8000 --env-file .env solar-panel-api-prod:latest
```

## 🔧 Service Details

### App Service
- **Image**: Built from Dockerfile
- **Port**: 8000 (API)
- **Environment**: See `.env.example` or `.env.docker`
- **Hot Reload**: Enabled (for development)

## 🧪 Testing

```bash
# Shell into container
./docker-dev.sh shell

# Test API
curl http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health
```

## 📊 Monitoring

### View real-time logs
```bash
docker-compose logs -f
```

### Check container stats
```bash
docker stats
```

### Inspect container
```bash
docker exec -it solar-panel-api ps aux
```

## 🛑 Troubleshooting

### Port already in use
```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Container won't start
```bash
# Check logs
docker-compose logs app

# Rebuild without cache
docker build --no-cache -t solar-panel-api:latest .
```

### Build fails
```bash
# Clear Docker cache
docker builder prune

# Rebuild from scratch
docker build --no-cache --progress=plain -t solar-panel-api:latest .
```

## 📦 Production Deployment

### Railway.app

```bash
# Railway will automatically detect Dockerfile
# Set environment variables in Railway dashboard
# Deploy with: git push
```

### Manual Docker deployment

```bash
# Build production image
docker build -f Dockerfile.prod -t your-registry/solar-panel-api:latest .
docker push your-registry/solar-panel-api:latest

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env.prod \
  --name solar-panel-api \
  your-registry/solar-panel-api:latest
```

## 📊 Image Sizes

- **Development**: ~300MB
- **Production**: ~280MB

## 🔐 Security Notes

1. Never commit `.env` file with secrets
2. Use strong JWT_SECRET_KEY in production
3. Use `--env-file` for production secrets
4. Don't use `--reload` flag in production
5. Keep Docker images updated

## 🔄 Updating

```bash
# Rebuild with latest code
docker-compose down
./docker-dev.sh build
./docker-dev.sh run
```

## 📝 Notes

- MQTT configuration is in `.env` file
- The app connects to MQTT broker specified in `MQTT_BROKER_HOST`
- For local MQTT testing, run Mosquitto separately or update MQTT_BROKER_HOST in `.env`