# Deployment Guide

This guide covers deploying SwarmGrid using Docker Compose for development and pilot environments.

## Prerequisites

### Software Requirements

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### Hardware Recommendations

| Component          | Minimum          | Recommended                         |
| ------------------ | ---------------- | ----------------------------------- |
| **Edge Device**    | x64 CPU, 4GB RAM | x64 CPU (AVX2), 8GB RAM, NVIDIA GPU |
| **Backend Server** | 2 vCPU, 4GB RAM  | 4 vCPU, 8GB RAM                     |

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/oguzhandede/SwarmGrid.git
cd SwarmGrid
```

### 2. Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor
```

Key settings to configure:

```env
# Your camera's RTSP URL
RTSP_URL=rtsp://user:password@camera-ip:554/stream

# Unique identifiers
CAMERA_ID=cam-01
ZONE_ID=zone-01
```

### 3. Configure Edge Agent

Edit `edge-agent/config/settings.yaml`:

```yaml
rtsp_url: "rtsp://user:pass@camera-ip:554/stream"
camera_id: "cam-01"
zone_id: "zone-01"
fps: 10
```

### 4. Start the Stack

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Service URLs

| Service     | URL                          | Default Credentials   |
| ----------- | ---------------------------- | --------------------- |
| Dashboard   | http://localhost:3002        | -                     |
| API         | http://localhost:5000        | -                     |
| Edge Stream | http://localhost:8000/stream | -                     |
| Grafana     | http://localhost:3001        | admin / swarmgrid     |
| Prometheus  | http://localhost:9090        | -                     |
| PostgreSQL  | localhost:5432               | swarmgrid / swarmgrid |
| Redis       | localhost:6379               | -                     |

## Service Management

### Start/Stop Services

```bash
# Start all
docker-compose up -d

# Stop all
docker-compose down

# Restart specific service
docker-compose restart core-backend

# View logs for specific service
docker-compose logs -f edge-agent
```

### Update Services

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Reset Data

```bash
# Stop services and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Troubleshooting

### Camera Connection Failed

1. **Verify RTSP URL works:**

   ```bash
   vlc rtsp://user:pass@camera-ip:554/stream
   ```

2. **Check network connectivity:**

   ```bash
   ping camera-ip
   ```

3. **View Edge Agent logs:**
   ```bash
   docker-compose logs -f edge-agent
   ```

### Database Connection Issues

1. **Wait for PostgreSQL health check:**

   ```bash
   docker-compose ps  # Check "healthy" status
   ```

2. **View database logs:**

   ```bash
   docker-compose logs -f postgres
   ```

3. **Connect manually:**
   ```bash
   docker-compose exec postgres psql -U swarmgrid -d swarmgrid
   ```

### Dashboard Not Loading

1. **Check Core Backend is running:**

   ```bash
   curl http://localhost:5000/health
   ```

2. **View Dashboard logs:**
   ```bash
   docker-compose logs -f dashboard
   ```

## Scaling

### Multiple Cameras

For each additional camera:

1. Create a new Edge Agent service in `docker-compose.override.yml`:

```yaml
services:
  edge-agent-2:
    build:
      context: ./edge-agent
    environment:
      - RTSP_URL=rtsp://user:pass@camera-2-ip:554/stream
      - CAMERA_ID=cam-02
      - ZONE_ID=zone-02
      - BACKEND_URL=http://core-backend:5000
```

2. Start the new agent:

```bash
docker-compose up -d edge-agent-2
```

### Production Deployment

For production environments, consider:

- **Kubernetes** for container orchestration
- **Managed PostgreSQL** for database reliability
- **Redis Cluster** for high availability
- **Load balancer** in front of Core Backend
- **CDN** for Dashboard assets

## Environment Variables Reference

### Edge Agent

| Variable      | Description              | Required |
| ------------- | ------------------------ | -------- |
| `RTSP_URL`    | Camera stream URL        | Yes      |
| `BACKEND_URL` | Core Backend API URL     | Yes      |
| `CAMERA_ID`   | Unique camera identifier | Yes      |
| `ZONE_ID`     | Zone identifier          | Yes      |
| `LOG_LEVEL`   | Logging verbosity        | No       |

### Core Backend

| Variable                        | Description         | Required |
| ------------------------------- | ------------------- | -------- |
| `ConnectionStrings__PostgreSQL` | Database connection | Yes      |
| `ConnectionStrings__Redis`      | Redis connection    | Yes      |
| `ASPNETCORE_ENVIRONMENT`        | Runtime mode        | No       |

### Dashboard

| Variable                     | Description           | Required |
| ---------------------------- | --------------------- | -------- |
| `NEXT_PUBLIC_API_URL`        | Core Backend URL      | Yes      |
| `NEXT_PUBLIC_EDGE_AGENT_URL` | Edge Agent stream URL | No       |
