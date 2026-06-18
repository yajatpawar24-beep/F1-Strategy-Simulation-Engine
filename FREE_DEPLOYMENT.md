# 💰 Free Deployment Options for F1 Strategy Engine

## Best Free Options (Ranked)

### 1. ✅ Google Cloud Run (Free Tier) - **RECOMMENDED**

**Free Tier Includes:**
- 2 million requests per month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds
- **This equals ~50-100 requests per day for free** (more than enough for testing/personal use)

**Setup (5 minutes):**
```bash
# 1. Install gcloud CLI
brew install google-cloud-sdk  # macOS
# Or download: https://cloud.google.com/sdk/docs/install

# 2. Login (uses free $300 credit for 90 days for new users!)
gcloud auth login

# 3. Create project (free)
gcloud projects create f1-strategy-engine-free --name="F1 Strategy Engine"
gcloud config set project f1-strategy-engine-free

# 4. Enable Cloud Run API (free)
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 5. Deploy (one command!)
gcloud run deploy f1-strategy-engine \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 1 \
  --allow-unauthenticated

# Get your FREE URL
gcloud run services describe f1-strategy-engine \
  --region us-central1 \
  --format='value(status.url)'
```

**Result:** `https://f1-strategy-engine-xxx-uc.a.run.app`

**Pros:**
- ✅ 100% free for low traffic (2M requests/month)
- ✅ Perfect for ML models
- ✅ Auto-scales to zero (no cost when idle)
- ✅ New users get $300 free credit for 90 days
- ✅ No credit card required for free tier

**Cons:**
- ⚠️ Cold starts (~5-10s) when idle
- ⚠️ Requires Google account

**Cost after free tier:** ~$10-20/month for moderate traffic

---

### 2. ✅ Hugging Face Spaces (Free Forever)

**Perfect for ML models!** Community tier is 100% free, no credit card needed.

**Setup (10 minutes):**

1. **Create account:** https://huggingface.co/join
2. **Create new Space:** https://huggingface.co/new-space
   - Name: `f1-strategy-engine`
   - SDK: `Docker`
   - Hardware: `CPU basic` (free)
   
3. **Create `Dockerfile` in Space:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY src/ ./src/
COPY data/registry/ ./data/registry/
COPY frontend/ ./frontend/

EXPOSE 7860

CMD ["uvicorn", "api.main_v2:app", "--host", "0.0.0.0", "--port", "7860"]
```

4. **Push your code:**
```bash
# Clone your Space
git clone https://huggingface.co/spaces/USERNAME/f1-strategy-engine
cd f1-strategy-engine

# Copy files
cp -r ~/Desktop/F1\ Strategy\ Simulation/* .

# Push
git add .
git commit -m "Add F1 Strategy Engine"
git push
```

**Result:** `https://huggingface.co/spaces/USERNAME/f1-strategy-engine`

**Pros:**
- ✅ 100% free forever
- ✅ No credit card required
- ✅ Designed for ML models
- ✅ 16GB RAM, 2 vCPU (free tier)
- ✅ Persistent storage
- ✅ Auto-builds on git push

**Cons:**
- ⚠️ Can sleep after inactivity (30 min wake-up time)
- ⚠️ Public by default (upgrade for private)

**Cost:** Always free for public projects

---

### 3. ✅ Railway.app (Free Trial)

**$5 free credit** (lasts 1-2 months with light usage)

**Setup (5 minutes):**

1. **Sign up:** https://railway.app (GitHub login)
2. **New Project** → Deploy from GitHub
3. **Select repo:** `F1-Strategy-Simulation-Engine`
4. **Railway auto-detects:** Dockerfile
5. **Deploy:** One click!

**Environment Variables:**
```
PORT=8000
PYTHONUNBUFFERED=1
```

**Result:** `https://f1-strategy-engine.up.railway.app`

**Pros:**
- ✅ Super easy setup (3 clicks)
- ✅ Auto-deploy on git push
- ✅ Good free tier ($5 credit)
- ✅ No cold starts

**Cons:**
- ⚠️ Free credit runs out (~1-2 months)
- ⚠️ Then $5-10/month

**Cost:** Free for 1-2 months, then $5-10/month

---

### 4. ✅ Oracle Cloud Always Free

**Truly free forever** with surprisingly good specs!

**Free Tier Includes:**
- 4 OCPUs (ARM Ampere A1)
- 24 GB RAM
- 200 GB storage
- Always free, no time limit

**Setup (20 minutes, more complex):**

1. **Create account:** https://www.oracle.com/cloud/free/
2. **Create Compute Instance:**
   - Shape: `VM.Standard.A1.Flex`
   - OCPUs: 4 (all free tier)
   - Memory: 24GB
   - Image: Ubuntu 22.04
3. **Install Docker:**
```bash
ssh ubuntu@YOUR_INSTANCE_IP

# Install Docker
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker ubuntu

# Clone repo
git clone https://github.com/yajatpawar24-beep/F1-Strategy-Simulation-Engine.git
cd F1-Strategy-Simulation-Engine

# Deploy
docker-compose up -d
```

4. **Open firewall:**
```bash
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
```

5. **Access:** `http://YOUR_INSTANCE_IP:8000`

**Pros:**
- ✅ 100% free forever
- ✅ Great specs (4 CPU, 24GB RAM)
- ✅ No credit card required after trial
- ✅ Full control

**Cons:**
- ⚠️ More complex setup
- ⚠️ Need to manage server
- ⚠️ ARM architecture (most packages work, but check)

**Cost:** Always free

---

### 5. ⚠️ Render (Limited Free Tier)

**Free tier but limited:**
- 512MB RAM (NOT ENOUGH for your models)
- Sleeps after 15 min of inactivity
- 750 hours/month

**Not recommended** for this project due to RAM limits.

---

### 6. ⚠️ Fly.io (Limited Free Tier)

**Free tier:**
- 3 shared-cpu VMs with 256MB RAM each
- Not enough for ML models

**Not recommended** for this project.

---

## 📊 Comparison Table

| Platform | Cost | RAM | CPU | Cold Start | Setup | ML-Friendly |
|----------|------|-----|-----|------------|-------|-------------|
| **Google Cloud Run** | Free* | 2GB | 2 vCPU | 5-10s | Easy | ✅ Perfect |
| **Hugging Face** | Free | 16GB | 2 vCPU | 30min | Easy | ✅ Perfect |
| **Railway** | $5 credit | 8GB | 2 vCPU | None | Very Easy | ✅ Good |
| **Oracle Always Free** | Free | 24GB | 4 vCPU | None | Hard | ✅ Good |
| **Render** | Free | 512MB | 0.5 vCPU | 30s | Easy | ❌ Too small |
| **Fly.io** | Free | 256MB | Shared | 1s | Medium | ❌ Too small |

*Free for 2M requests/month + $300 credit for new users

---

## 🎯 Recommended Strategy

### For Testing/Personal Use:
**Use Google Cloud Run Free Tier**
- 2M requests/month = ~66 requests/day
- Perfect for testing and demos
- New users get $300 credit (3-6 months free)

### For Public Demo:
**Use Hugging Face Spaces**
- 100% free forever
- Perfect for portfolio projects
- Great for sharing with community

### For Long-Term Free:
**Use Oracle Cloud Always Free**
- Truly free forever
- Best specs (24GB RAM!)
- Requires more setup

---

## 🚀 Quickest Free Setup (5 minutes)

### Option A: Google Cloud Run (Best for ML)

```bash
# 1. Install CLI
brew install google-cloud-sdk

# 2. Login & setup
gcloud auth login
gcloud projects create f1-engine-free
gcloud config set project f1-engine-free
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# 3. Deploy
cd "/Users/yajatpawar/Desktop/F1 Strategy Simulation"
gcloud run deploy f1-strategy-engine \
  --source . \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated

# Done! URL: https://f1-strategy-engine-xxx.run.app
```

### Option B: Hugging Face Spaces (100% Free)

```bash
# 1. Create account at https://huggingface.co/join

# 2. Create Space at https://huggingface.co/new-space
#    - Name: f1-strategy-engine
#    - SDK: Docker
#    - Hardware: CPU basic

# 3. Clone & push
git clone https://huggingface.co/spaces/USERNAME/f1-strategy-engine
cd f1-strategy-engine
cp -r ~/Desktop/F1\ Strategy\ Simulation/* .
git add .
git commit -m "Add F1 Strategy Engine"
git push

# Done! URL: https://huggingface.co/spaces/USERNAME/f1-strategy-engine
```

---

## 💡 Cost Optimization Tips

### For Google Cloud Run:
1. **Set min instances to 0** (auto-scale to zero)
2. **Use 1-2GB RAM** instead of 4GB
3. **Set max instances to 1** for free tier
4. **Enable CPU throttling** when idle

**Config:**
```bash
gcloud run deploy f1-strategy-engine \
  --min-instances 0 \
  --max-instances 1 \
  --memory 2Gi \
  --cpu 1 \
  --cpu-throttling
```

### For Railway:
1. **Remove unused services**
2. **Set sleep after inactivity**
3. **Monitor usage dashboard**

---

## 🆘 Troubleshooting

### "Out of memory" errors:
- Reduce model size
- Use model quantization
- Split into microservices

### Cold starts too slow:
- Use Google Cloud Run (fastest free option)
- Or upgrade to Railway (no cold starts)

### Free tier expired:
- Oracle Cloud Always Free (never expires)
- Or use Hugging Face Spaces (free forever)

---

## 🎉 Final Recommendation

**Start with Google Cloud Run Free Tier:**
1. New users get $300 credit (90 days)
2. After that: 2M requests/month free
3. Perfect for ML models
4. 5-minute setup

**Then explore:**
- Hugging Face for 100% free public hosting
- Oracle Cloud for long-term free with best specs

---

## 📞 Need Help?

1. Check `DEPLOYMENT.md` for detailed guides
2. Check `DOCKER_SETUP.md` for Docker commands
3. Use `./deploy.sh` for local testing first

**Quick Links:**
- Google Cloud Free Tier: https://cloud.google.com/free
- Hugging Face Spaces: https://huggingface.co/spaces
- Railway: https://railway.app
- Oracle Cloud: https://www.oracle.com/cloud/free/

---

**TL;DR:** Use **Google Cloud Run** (2M requests/month free + $300 credit) or **Hugging Face Spaces** (100% free forever). Both support ML models and are easy to set up.
