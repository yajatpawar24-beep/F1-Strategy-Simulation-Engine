# F1 Strategy Engine - Deployment Guide

## 🐳 Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 5GB disk space

### Quick Start (Development)

```bash
# Build and run
docker-compose up --build

# Access the application
# Frontend: http://localhost:8000/frontend/index_v3.html
# API: http://localhost:8000/api/v1/predictions/strategic
# Health: http://localhost:8000/health
```

### Production Deployment (with Nginx)

```bash
# Build and run with nginx reverse proxy
docker-compose --profile production up --build -d

# Access the application
# Frontend: http://localhost/
# API: http://localhost/api/v1/predictions/strategic
# Health: http://localhost/health
```

### Docker Commands

```bash
# Build image
docker build -t f1-strategy-engine .

# Run container
docker run -d -p 8000:8000 --name f1-engine f1-strategy-engine

# View logs
docker logs -f f1-engine

# Stop container
docker stop f1-engine

# Remove container
docker rm f1-engine

# Check health
docker inspect --format='{{.State.Health.Status}}' f1-engine
```

## 📦 What's Included

### Application Structure
```
/app
├── api/                    # FastAPI application
│   ├── main_v2.py         # API entry point
│   ├── models.py          # Pydantic schemas
│   ├── dependencies.py    # Shared dependencies
│   └── routers/           # API routes
├── src/                   # Source code
│   └── inference/         # ML inference logic
├── data/registry/         # Pre-trained models (5 .pkl files)
│   ├── m1_pipeline.pkl   # Lap time regressor
│   ├── m2_pipeline.pkl   # Pit lap classifier
│   ├── m3_pipeline.pkl   # Pit-in-3 classifier
│   ├── m4_pipeline.pkl   # Long horizon regressor
│   └── m5_pipeline.pkl   # Short horizon regressor
└── frontend/              # Dashboard UI
    ├── index_v3.html     # Main dashboard
    ├── styles_v3.css     # Styles
    └── app_v3.js         # API integration
```

### Model Files
Total size: ~50MB (5 pre-trained ML models)
- Ensure `data/registry/*.pkl` files exist before building

## 🚀 Cloud Deployment Options

### AWS ECS (Elastic Container Service)

```bash
# 1. Build and tag image
docker build -t f1-strategy-engine .
docker tag f1-strategy-engine:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/f1-strategy-engine:latest

# 2. Push to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/f1-strategy-engine:latest

# 3. Create ECS task definition and service
# Use Fargate with 2 vCPU, 4GB RAM
```

### Google Cloud Run

```bash
# 1. Build and push
gcloud builds submit --tag gcr.io/<project-id>/f1-strategy-engine

# 2. Deploy
gcloud run deploy f1-strategy-engine \
  --image gcr.io/<project-id>/f1-strategy-engine \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --port 8000 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# 1. Build and push to ACR
az acr build --registry <registry-name> --image f1-strategy-engine .

# 2. Deploy
az container create \
  --resource-group <resource-group> \
  --name f1-strategy-engine \
  --image <registry-name>.azurecr.io/f1-strategy-engine:latest \
  --cpu 2 \
  --memory 4 \
  --port 8000 \
  --dns-name-label f1-strategy
```

### DigitalOcean App Platform

```bash
# 1. Push to Docker Hub or GHCR
docker tag f1-strategy-engine:latest <username>/f1-strategy-engine:latest
docker push <username>/f1-strategy-engine:latest

# 2. Create app via DO console or CLI
doctl apps create --spec app.yaml
```

### Kubernetes (k8s)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: f1-strategy-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: f1-strategy-engine
  template:
    metadata:
      labels:
        app: f1-strategy-engine
    spec:
      containers:
      - name: f1-strategy-engine
        image: f1-strategy-engine:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: f1-strategy-service
spec:
  selector:
    app: f1-strategy-engine
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional environment variables
PYTHONUNBUFFERED=1          # Python output buffering
LOG_LEVEL=info              # Logging level (debug, info, warning, error)
WORKERS=1                   # Number of Uvicorn workers
MAX_REQUESTS=1000           # Max requests per worker before restart
```

### Frontend API URL

Update `app_v3.js` for production:

```javascript
// Development
const API_URL = 'http://localhost:8000';

// Production (same domain)
const API_URL = '';  // Relative URLs

// Production (different domain)
const API_URL = 'https://api.f1-strategy.com';
```

## 📊 Resource Requirements

### Minimum (Development)
- CPU: 1 vCPU
- RAM: 2GB
- Disk: 2GB

### Recommended (Production)
- CPU: 2 vCPUs
- RAM: 4GB
- Disk: 5GB
- Load Balancer for high availability

### Scaling Considerations
- Each model prediction: ~200ms (varies by complexity)
- Memory usage: ~1.5GB (5 models loaded)
- Concurrent requests: 10-50 (single container)
- For >100 concurrent users: Use horizontal scaling (multiple containers)

## 🔐 Security Checklist

- [ ] Enable CORS only for trusted domains
- [ ] Add rate limiting (recommended: 100 req/min per IP)
- [ ] Use HTTPS in production
- [ ] Set up authentication if needed
- [ ] Enable firewall rules (allow only port 80/443)
- [ ] Keep dependencies updated
- [ ] Monitor logs for suspicious activity
- [ ] Use secrets management for API keys (if any)

## 📈 Monitoring

### Health Checks
```bash
# Docker health status
docker inspect --format='{{.State.Health.Status}}' f1-engine

# API health endpoint
curl http://localhost:8000/health
```

### Logs
```bash
# Docker logs
docker logs -f f1-engine

# View last 100 lines
docker logs --tail 100 f1-engine
```

### Metrics to Monitor
- API response time
- Request rate
- Error rate
- CPU/Memory usage
- Model inference time

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs f1-engine

# Common issues:
# - Missing model files in data/registry/
# - Port 8000 already in use
# - Insufficient memory
```

### Models not loading
```bash
# Verify model files exist
docker exec f1-engine ls -lh /app/data/registry/

# Should show 5 .pkl files (~10MB each)
```

### API returns 500 errors
```bash
# Check prediction endpoint
docker exec f1-engine python -c "
from src.inference.strategic_predictor import StrategicPredictor
predictor = StrategicPredictor()
print('Models loaded successfully')
"
```

### Frontend can't connect to API
- Check CORS settings in `api/main_v2.py`
- Verify API_URL in `frontend/app_v3.js`
- Ensure container is running: `docker ps`

## 📝 CI/CD Pipeline Example

### GitHub Actions (.github/workflows/deploy.yml)

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t f1-strategy-engine .
      
      - name: Run tests
        run: docker run f1-strategy-engine pytest
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag f1-strategy-engine:latest ${{ secrets.DOCKER_USERNAME }}/f1-strategy-engine:latest
          docker push ${{ secrets.DOCKER_USERNAME }}/f1-strategy-engine:latest
```

## 🎯 Production Checklist

Before deploying to production:

- [ ] Build and test Docker image locally
- [ ] Verify all 5 model files are included
- [ ] Test API endpoints (/health, /predict)
- [ ] Test frontend functionality
- [ ] Configure CORS for production domain
- [ ] Update API_URL in frontend
- [ ] Set up SSL certificate
- [ ] Configure environment variables
- [ ] Set up monitoring/alerting
- [ ] Prepare rollback plan
- [ ] Document deployment process
- [ ] Test health checks
- [ ] Load test with expected traffic

## 📞 Support

For issues or questions:
1. Check logs: `docker logs f1-engine`
2. Verify health: `curl http://localhost:8000/health`
3. Review this guide
4. Check API documentation: `http://localhost:8000/docs`
