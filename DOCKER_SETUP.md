# 🐳 Docker Setup & Deployment Summary

## ✅ Files Created for Deployment

### Core Docker Files
- **Dockerfile** - Production-ready Python 3.11 image with all dependencies
- **docker-compose.yml** - Stack with API + optional Nginx reverse proxy
- **.dockerignore** - Optimized Docker build (excludes unnecessary files)
- **nginx.conf** - Reverse proxy configuration for production

### Helper Scripts & Documentation
- **deploy.sh** - Convenient deployment script with all commands
- **DEPLOYMENT.md** - Comprehensive deployment guide (AWS, GCP, Azure, K8s)
- **DOCKER_SETUP.md** - This file (quick reference)

## 🚀 Quick Start

### 1. Start Docker Desktop
```bash
# Make sure Docker Desktop is running
open -a Docker
```

### 2. Build & Deploy
```bash
# Simple deployment
./deploy.sh build
./deploy.sh start

# Or using Docker Compose
docker-compose up --build -d
```

### 3. Access Application
- **Frontend**: http://localhost:8000/frontend/index_v3.html
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## 📦 What's Included in the Docker Image

### Application Stack
```
Python 3.11 (slim)
├── FastAPI Backend (api/)
├── ML Models (data/registry/ - 5 .pkl files ~50MB)
├── Inference Logic (src/inference/)
└── Frontend Dashboard (frontend/)
```

### Dependencies Installed
- FastAPI, Uvicorn (API server)
- Scikit-learn, LightGBM, CatBoost (ML)
- NumPy, Pandas (data processing)
- Pydantic (validation)
- All from requirements.txt

### Ports Exposed
- **8000** - API & Frontend access

### Health Checks
- Automatic health monitoring every 30s
- Endpoint: `GET /health`
- Returns: `{"status":"healthy","models_loaded":5,"api_version":"2.0.0"}`

## 🛠️ Deployment Commands

### Using deploy.sh Script
```bash
./deploy.sh build          # Build Docker image
./deploy.sh start          # Start container
./deploy.sh stop           # Stop container
./deploy.sh restart        # Restart container
./deploy.sh logs           # View logs (Ctrl+C to exit)
./deploy.sh health         # Check health status
./deploy.sh clean          # Remove container & image
./deploy.sh compose-up     # Start with Docker Compose
./deploy.sh compose-down   # Stop Docker Compose stack
```

### Using Docker CLI
```bash
# Build
docker build -t f1-strategy-engine .

# Run
docker run -d -p 8000:8000 --name f1-engine f1-strategy-engine

# Logs
docker logs -f f1-engine

# Stop
docker stop f1-engine

# Remove
docker rm f1-engine
```

### Using Docker Compose
```bash
# Start
docker-compose up --build -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart
```

## 🌐 Production Deployment with Nginx

For production with reverse proxy:

```bash
# Start with Nginx profile
docker-compose --profile production up --build -d
```

This starts:
- **f1-strategy-engine** (API container on :8000)
- **nginx** (reverse proxy on :80)

Access via:
- Frontend: http://localhost/
- API: http://localhost/api/*

## ☁️ Cloud Deployment Options

### AWS (ECS/Fargate)
```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-url>
docker tag f1-strategy-engine:latest <ecr-url>:latest
docker push <ecr-url>:latest

# Deploy via ECS console or CLI
```

### Google Cloud Run
```bash
# Build & Deploy
gcloud builds submit --tag gcr.io/<project-id>/f1-strategy-engine
gcloud run deploy --image gcr.io/<project-id>/f1-strategy-engine --memory 4Gi --cpu 2
```

### DigitalOcean App Platform
```bash
# Push to Docker Hub
docker tag f1-strategy-engine:latest <username>/f1-strategy-engine:latest
docker push <username>/f1-strategy-engine:latest

# Deploy via DO console
```

See **DEPLOYMENT.md** for detailed cloud deployment instructions.

## 📊 Resource Requirements

### Development
- **CPU**: 1 vCPU
- **RAM**: 2GB
- **Disk**: 2GB

### Production
- **CPU**: 2 vCPUs (recommended)
- **RAM**: 4GB (recommended)
- **Disk**: 5GB
- **Concurrent**: 10-50 requests per container

### Scaling
- Single container: ~200ms per prediction
- For >100 concurrent users: Use horizontal scaling (multiple containers + load balancer)

## 🔐 Security Checklist

Before production deployment:

- [ ] Update CORS in `api/main_v2.py` to trusted domains only
- [ ] Change API_URL in `frontend/app_v3.js` to production URL
- [ ] Enable HTTPS (use Let's Encrypt or cloud provider SSL)
- [ ] Add rate limiting (recommended: 100 req/min per IP)
- [ ] Set up firewall rules (allow only 80/443)
- [ ] Enable authentication if needed
- [ ] Use secrets management for sensitive data
- [ ] Set up monitoring/alerting

## 🐛 Troubleshooting

### Docker daemon not running
```bash
# Start Docker Desktop
open -a Docker
```

### Port 8000 already in use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
docker run -d -p 8080:8000 f1-strategy-engine
```

### Models not loading
```bash
# Verify model files exist before building
ls -lh data/registry/*.pkl

# Should show 5 files:
# m1_pipeline.pkl (~10MB)
# m2_pipeline.pkl (~8MB)
# m3_pipeline.pkl (~8MB)
# m4_pipeline.pkl (~12MB)
# m5_pipeline.pkl (~12MB)
```

### Frontend can't connect to API
1. Check CORS settings in `api/main_v2.py`
2. Verify API_URL in `frontend/app_v3.js`
3. Ensure container is running: `docker ps`
4. Check logs: `docker logs f1-engine`

### Container crashes immediately
```bash
# View logs for error message
docker logs f1-engine

# Common issues:
# - Missing dependencies
# - Model files not found
# - Port conflict
```

## 📝 Configuration

### Environment Variables
Edit `docker-compose.yml` or pass with `-e` flag:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - LOG_LEVEL=info
  - WORKERS=1
```

### Frontend API URL
For production, update `frontend/app_v3.js`:

```javascript
// Development
const API_URL = 'http://localhost:8000';

// Production (same domain)
const API_URL = '';  // Uses relative URLs

// Production (different domain)
const API_URL = 'https://api.yourdomain.com';
```

## ✅ Deployment Checklist

Before pushing to production:

1. **Build & Test Locally**
   - [ ] Build Docker image successfully
   - [ ] Test API endpoints (/health, /predict)
   - [ ] Test frontend functionality
   - [ ] Verify all 5 models load correctly

2. **Configuration**
   - [ ] Update CORS settings for production domain
   - [ ] Update API_URL in frontend
   - [ ] Set environment variables
   - [ ] Configure SSL certificate

3. **Monitoring**
   - [ ] Set up health check monitoring
   - [ ] Configure logging/alerting
   - [ ] Set up performance monitoring
   - [ ] Prepare rollback plan

4. **Security**
   - [ ] Enable HTTPS
   - [ ] Add rate limiting
   - [ ] Restrict CORS to trusted domains
   - [ ] Set up firewall rules
   - [ ] Review security best practices

5. **Documentation**
   - [ ] Document deployment process
   - [ ] Create runbook for common issues
   - [ ] Document API endpoints
   - [ ] Prepare incident response plan

## 📞 Next Steps

1. **Start Docker Desktop** (if not running)
2. **Run**: `./deploy.sh build && ./deploy.sh start`
3. **Open**: http://localhost:8000/frontend/index_v3.html
4. **Test**: Make a prediction!

For production deployment, see **DEPLOYMENT.md**.

---

**Ready to deploy! 🏁**
