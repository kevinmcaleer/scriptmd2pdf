# ScriptMD2PDF Deployment Guide

## Overview

This guide covers deploying ScriptMD2PDF as a containerized web application on a Raspberry Pi using Docker.

## Prerequisites

- Raspberry Pi 3B+ or newer (ARM64 or ARM32)
- Docker installed on Raspberry Pi
- Access to private Docker registry at 192.168.2.1:5000
- At least 512MB available RAM
- Network connectivity

## Quick Start

### 1. Pull the Image

```bash
docker pull 192.168.2.1:5000/md2script:latest
```

### 2. Run with Docker Compose

```bash
# Clone the repository or copy docker-compose.yml
git clone https://github.com/kevinmcaleer/scriptmd2pdf.git
cd scriptmd2pdf

# Start the service
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access the Application

Open your browser and navigate to:
- Local: `http://localhost:8000`
- Network: `http://<raspberry-pi-ip>:8000`

## Manual Docker Run

If you prefer not to use docker-compose:

```bash
docker run -d \
  --name scriptmd2pdf \
  --restart unless-stopped \
  -p 8000:8000 \
  -e MAX_FILE_SIZE=1048576 \
  -e RATE_LIMIT=5/minute \
  --memory=1g \
  --cpus=2 \
  192.168.2.1:5000/md2script:latest
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | 0.0.0.0 | Bind address |
| `PORT` | 8000 | Port number |
| `MAX_FILE_SIZE` | 1048576 | Maximum upload size (1MB) |
| `RATE_LIMIT` | 5/minute | Rate limit per IP |
| `PYTHONUNBUFFERED` | 1 | Disable Python output buffering |

### Custom Configuration

Create a `.env` file:

```bash
MAX_FILE_SIZE=2097152  # 2MB
RATE_LIMIT=10/minute
PORT=8080
```

Update docker-compose.yml:

```yaml
services:
  scriptmd2pdf:
    env_file:
      - .env
```

## Resource Limits

### Recommended for Raspberry Pi 4

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 256M
```

### For Raspberry Pi 3B+

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 128M
```

## Monitoring

### Health Checks

The container includes a built-in health check:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' scriptmd2pdf

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' scriptmd2pdf
```

### Manual Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T13:00:00.000000"
}
```

### View Logs

```bash
# Follow logs
docker logs -f scriptmd2pdf

# Last 100 lines
docker logs --tail 100 scriptmd2pdf

# With timestamps
docker logs -t scriptmd2pdf
```

## Maintenance

### Update to Latest Version

```bash
# Pull latest image
docker pull 192.168.2.1:5000/md2script:latest

# Restart with new image
docker-compose down
docker-compose up -d

# Clean up old images
docker image prune -f
```

### Backup and Restore

The application is stateless, so no backup is needed. However, you may want to backup configuration:

```bash
# Backup configuration
cp docker-compose.yml docker-compose.yml.backup
cp .env .env.backup

# Restore
cp docker-compose.yml.backup docker-compose.yml
cp .env.backup .env
docker-compose up -d
```

## Troubleshooting

### Container Won't Start

```bash
# Check container status
docker ps -a

# View error logs
docker logs scriptmd2pdf

# Check resource usage
docker stats scriptmd2pdf
```

### Out of Memory

Reduce memory limits or close other applications:

```bash
# Check system memory
free -h

# Reduce container memory limit
docker update --memory=512m scriptmd2pdf
```

### Port Already in Use

Change the port mapping:

```yaml
ports:
  - "8080:8000"  # Use port 8080 instead
```

### Connection Refused

Verify the service is running and port is accessible:

```bash
# Check if service is listening
docker exec scriptmd2pdf netstat -tuln | grep 8000

# Test from host
curl http://localhost:8000/health

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp
```

### Rate Limit Issues

Adjust rate limiting:

```bash
# Increase rate limit
docker-compose down
# Edit docker-compose.yml or .env
RATE_LIMIT=10/minute
docker-compose up -d
```

## Security Best Practices

### 1. Run Behind Reverse Proxy

Use Nginx or Traefik for HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name md2script.kevs.wtf;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Network Isolation

Use Docker networks:

```yaml
networks:
  scriptmd2pdf-network:
    driver: bridge
    internal: false
```

### 3. Update Regularly

```bash
# Check for updates weekly
docker pull 192.168.2.1:5000/md2script:latest
docker-compose up -d
```

### 4. Monitor Logs

Set up log rotation:

```yaml
services:
  scriptmd2pdf:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Performance Optimization

### 1. Enable Docker BuildKit

```bash
export DOCKER_BUILDKIT=1
```

### 2. Use Docker Layer Caching

Already configured in Dockerfile with multi-stage builds.

### 3. Limit Container Resources

Prevents one container from consuming all resources:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
```

## CI/CD Integration

### GitHub Actions Workflow

The repository includes a GitHub Actions workflow that:
1. Runs tests on every push/PR
2. Checks code coverage (minimum 80%)
3. Builds multi-platform Docker images
4. Pushes to private registry
5. Creates releases for version tags

### Manual Build and Push

```bash
# Build for Raspberry Pi (ARM64)
docker buildx build --platform linux/arm64 -t 192.168.2.1:5000/md2script:latest --push .

# Build for Raspberry Pi 3 (ARM32)
docker buildx build --platform linux/arm/v7 -t 192.168.2.1:5000/md2script:latest --push .

# Build multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t 192.168.2.1:5000/md2script:latest \
  --push .
```

## Testing the Deployment

### 1. Basic Functionality Test

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test file upload
curl -X POST -F "file=@example_screenplay.md" \
  http://localhost:8000/convert \
  -o test_output.pdf

# Verify PDF was created
file test_output.pdf
```

### 2. Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health
```

### 3. Rate Limit Testing

```bash
# Send 10 requests rapidly
for i in {1..10}; do
  curl -X POST -F "file=@example_screenplay.md" \
    http://localhost:8000/convert \
    -o test_$i.pdf &
done
wait

# Should see rate limit errors (429) after 5 requests
```

## Production Checklist

- [ ] Configure reverse proxy with HTTPS
- [ ] Set up log aggregation
- [ ] Configure monitoring and alerts
- [ ] Set resource limits appropriate for your hardware
- [ ] Enable automatic container restart
- [ ] Set up backup for configuration files
- [ ] Test disaster recovery procedure
- [ ] Document custom configuration
- [ ] Set up rate limiting at reverse proxy level
- [ ] Configure firewall rules
- [ ] Test health check endpoints
- [ ] Verify log rotation is working
- [ ] Set up automated updates

## Support

For issues or questions:
- GitHub Issues: https://github.com/kevinmcaleer/scriptmd2pdf/issues
- Documentation: See `design/epic.md` for implementation details
- API Documentation: Visit `http://localhost:8000/docs` (FastAPI auto-generated)

## License

See LICENSE file in the repository root.
