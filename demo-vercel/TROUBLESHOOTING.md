# Troubleshooting Vercel Deployment

## Common Issues and Solutions

### 404 Error (Route Not Found)

**Error:** `404: NOT_FOUND` with code like `sfo1::ppwwq-1771122361111-dfcc04219204`

**Causes:**
1. Routes not configured correctly in `vercel.json`
2. Files in wrong directory structure
3. Cache issue

**Solutions:**

**1. Check file structure:**
```bash
# Should look like this:
demo-vercel/
├── api/
│   └── index.py
├── public/
│   └── index.html
└── vercel.json
```

**2. Verify vercel.json is correct:**
```bash
# Run from demo-vercel/ directory
cat vercel.json
```

**3. Clear cache and redeploy:**
```bash
# Force fresh deployment
vercel --prod --force
```

**4. Check Vercel build logs:**
```bash
# View real-time logs
vercel logs --follow

# Or check in dashboard:
# https://vercel.com/[username]/[project]/deployments
```

**5. Test routes individually:**
```bash
# Test API health endpoint
curl https://your-app.vercel.app/api/health

# Should return: {"status":"healthy",...}
```

---

### Environment Variable Not Set

**Error:** `"OpenRouter API key not configured"`

**Solution:**
```bash
# Add environment variable
vercel env add OPENROUTER_API_KEY

# Paste your API key when prompted

# Redeploy to apply changes
vercel --prod
```

**Verify it's set:**
```bash
# List all environment variables
vercel env ls
```

---

### Build Fails

**Error:** Build logs show Python errors

**Common causes:**

**1. Python version mismatch:**
```bash
# Vercel uses Python 3.9 by default
# Check requirements.txt compatibility
```

**2. Missing dependencies:**
```bash
# Verify requirements.txt includes:
Flask==3.0.0
requests==2.31.0
Werkzeug==3.0.1
```

**3. Syntax errors:**
```bash
# Test locally first:
cd api
python index.py

# Should run without errors
```

---

### API Timeout

**Error:** Function timed out

**Cause:** OpenRouter API taking too long (>10 seconds on Hobby tier)

**Solutions:**

**1. Upgrade to Vercel Pro** ($20/month) - 60s timeout

**2. Use faster model:**
Edit `vercel.json` or environment variable:
```json
{
  "env": {
    "OPENROUTER_MODEL": "anthropic/claude-3-haiku"
  }
}
```

**3. Reduce timeout on OpenRouter side:**
Edit `api/index.py` line ~76:
```python
timeout=25  # Reduce to 8 for Hobby tier
```

---

### CORS Errors

**Error:** `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solution:**

Add CORS headers to Flask app in `api/index.py`:
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

Add to `requirements.txt`:
```
flask-cors==4.0.0
```

---

### Image Upload Fails

**Error:** `File too large` or `Request Entity Too Large`

**Cause:** Vercel has a 4.5 MB request limit (Hobby tier)

**Solutions:**

**1. Client-side compression** (recommended):
Already implemented in `public/index.html` with file size check

**2. Warn users:**
The UI already shows "Max size: 4.5 MB"

**3. Upgrade to Pro:**
Vercel Pro allows 50 MB requests

---

## Debugging Steps

### 1. Check Deployment Status

```bash
# List recent deployments
vercel ls

# Check specific deployment
vercel inspect [deployment-url]
```

### 2. View Logs

```bash
# Real-time logs
vercel logs --follow

# Filter by function
vercel logs --follow --function api/index.py
```

### 3. Test Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export OPENROUTER_API_KEY="your_key"

# Run locally
cd api
python index.py

# Test in browser: http://localhost:5000
```

### 4. Check Environment Variables

```bash
# List all env vars
vercel env ls

# Should see:
# OPENROUTER_API_KEY (Production)
# OPENROUTER_MODEL (Production)
```

### 5. Verify File Permissions

```bash
# Make sure files are readable
chmod 644 api/index.py
chmod 644 public/index.html
chmod 644 vercel.json
```

---

## Getting Help

### 1. Check Vercel Status
https://vercel-status.com

### 2. View Build Logs
https://vercel.com/[username]/[project]/deployments → Click deployment → View logs

### 3. Check OpenRouter Status
https://status.openrouter.ai

### 4. Enable Debug Mode

In `api/index.py`, add:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 5. Test API Directly

```bash
# Test health endpoint
curl https://your-app.vercel.app/api/health

# Expected response:
# {"status":"healthy","api_configured":true,"model":"..."}
```

### 6. Test Prediction

```bash
# Create test payload
cat > test.json << 'EOF'
{
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
EOF

# Test prediction endpoint
curl -X POST https://your-app.vercel.app/api/predict \
  -H "Content-Type: application/json" \
  -d @test.json
```

---

## Quick Fixes

### Force Redeploy
```bash
vercel --prod --force
```

### Clear Local Cache
```bash
rm -rf .vercel
vercel --prod
```

### Start Fresh
```bash
# Remove project from Vercel
vercel remove [project-name]

# Deploy again
vercel --prod
```

### Rollback to Previous Deployment
```bash
# List deployments
vercel ls

# Promote previous deployment to production
vercel promote [deployment-url]
```

---

## Still Having Issues?

1. **Check this README:** Make sure you followed all steps
2. **View Vercel docs:** https://vercel.com/docs/functions/serverless-functions/runtimes/python
3. **OpenRouter docs:** https://openrouter.ai/docs
4. **GitHub Issues:** Open an issue with:
   - Error message
   - Deployment URL
   - Build logs
   - Steps to reproduce

---

**Most common fix:** Redeploy with `vercel --prod --force` ✨
