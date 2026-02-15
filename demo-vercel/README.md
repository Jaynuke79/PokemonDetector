# Pokemon Detector - Vercel Demo

A serverless Pokemon detector deployed on Vercel using OpenRouter's vision AI APIs. Click a link, upload an image, get predictions instantly!

## 🚀 Live Demo

Once deployed, you'll get a URL like: `https://pokemon-detector-demo.vercel.app`

## ✨ Features

- **Instant deployment** - Deploy in 2 minutes
- **Free hosting** - Vercel's free tier
- **Serverless** - Auto-scales, pay only for usage
- **Public URL** - Share with anyone
- **No model files** - Uses OpenRouter API (Claude 3.5 Sonnet)

## 📋 Prerequisites

1. **OpenRouter Account**
   - Sign up at [openrouter.ai](https://openrouter.ai/)
   - Get API key from [openrouter.ai/keys](https://openrouter.ai/keys)
   - Add $5 credits to your account

2. **Vercel Account** (free)
   - Sign up at [vercel.com](https://vercel.com)

3. **Node.js** (for Vercel CLI)
   - Install from [nodejs.org](https://nodejs.org/)

## 🎯 Quick Deploy (2 Minutes)

### Option 1: One-Click Deploy (Easiest!)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/pokemonDetector/tree/main/demo-vercel&env=OPENROUTER_API_KEY&envDescription=OpenRouter%20API%20Key%20from%20openrouter.ai/keys)

1. Click the button above
2. Connect your GitHub account
3. Add environment variable:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
4. Click "Deploy"
5. Get your live URL! 🎉

### Option 2: Vercel CLI

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Navigate to demo-vercel directory
cd demo-vercel

# 3. Login to Vercel (opens browser)
vercel login

# 4. Add your OpenRouter API key
vercel env add OPENROUTER_API_KEY

# Paste your API key when prompted

# 5. Deploy!
vercel --prod

# 6. You'll get a URL like: https://pokemon-detector-xyz.vercel.app
```

**That's it!** Your demo is live!

### Option 3: GitHub Integration (Auto-Deploy)

```bash
# 1. Push demo-vercel to GitHub
git add demo-vercel/
git commit -m "Add Vercel demo"
git push

# 2. Go to vercel.com
# 3. Click "Add New Project"
# 4. Import your GitHub repository
# 5. Set Root Directory to: demo-vercel
# 6. Add environment variable:
#    - OPENROUTER_API_KEY: your_key_here
# 7. Click "Deploy"

# Now every git push auto-deploys! 🚀
```

## 🔧 Configuration

### Environment Variables

Set in Vercel Dashboard or via CLI:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ Yes | - | Your OpenRouter API key |
| `OPENROUTER_MODEL` | ❌ No | `anthropic/claude-3.5-sonnet` | AI model to use |

### Changing the Model

Edit `vercel.json` or set environment variable:

```json
{
  "env": {
    "OPENROUTER_MODEL": "openai/gpt-4-vision-preview"
  }
}
```

**Available Models:**
- `anthropic/claude-3.5-sonnet` (recommended) - Best accuracy, ~$0.003/image
- `openai/gpt-4-vision-preview` - Good accuracy, ~$0.01/image
- `anthropic/claude-3-haiku` - Fastest, cheapest, ~$0.0003/image
- `google/gemini-pro-vision` - Good balance, ~$0.001/image

## 📁 Project Structure

```
demo-vercel/
├── api/
│   └── index.py              # Serverless API endpoint
├── public/
│   └── index.html            # Frontend UI
├── vercel.json               # Vercel configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🧪 Local Testing

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variable
export OPENROUTER_API_KEY="your_key_here"

# 3. Run Flask app
cd api
python index.py

# 4. Open browser
# Visit: http://localhost:5000
```

**Note:** Local testing won't work exactly like Vercel (different routing), but the API logic can be tested.

## 💰 Cost Breakdown

### Vercel (Free Tier)
- ✅ **100 GB bandwidth/month** - More than enough for demos
- ✅ **100 GB-hours compute** - Plenty for serverless functions
- ✅ **Unlimited deployments**
- ✅ **Automatic HTTPS**
- **Cost:** $0

### OpenRouter API
Assuming Claude 3.5 Sonnet (~$0.003 per image):

| Usage | Images/Month | Cost |
|-------|--------------|------|
| Light demo | 100 | $0.30 |
| Medium demo | 500 | $1.50 |
| Popular demo | 2000 | $6.00 |
| Viral demo | 10000 | $30.00 |

**Total Cost:** ~$0-6/month for typical demo usage

## 🔍 Monitoring

### View Logs

```bash
# Real-time logs
vercel logs --follow

# Or check Vercel Dashboard:
# https://vercel.com/dashboard -> Your Project -> Logs
```

### Analytics

Vercel provides built-in analytics:
- Request counts
- Response times
- Error rates
- Geographic distribution

Access at: `https://vercel.com/[username]/[project]/analytics`

## 🐛 Troubleshooting

### "API key not configured"

**Solution:**
```bash
# Add the environment variable
vercel env add OPENROUTER_API_KEY

# Or via Vercel Dashboard:
# Settings → Environment Variables → Add
```

### "File too large" error

**Cause:** Vercel has a 4.5 MB request limit

**Solution:** The UI already limits uploads to 4.5 MB. If users bypass this:
- Compress images before upload
- Or upgrade to Vercel Pro ($20/month) for 50 MB limit

### Slow responses

**Cause:** OpenRouter API can take 2-5 seconds

**Solutions:**
- Switch to faster model (`claude-3-haiku`)
- Add loading indicators (already included)
- Consider caching common predictions

### CORS errors

**Cause:** API route configuration issue

**Solution:** Check `vercel.json` routes are correct:
```json
{
  "routes": [
    {"src": "/api/(.*)", "dest": "api/index.py"},
    {"src": "/(.*)", "dest": "public/$1"}
  ]
}
```

### Deployment fails

**Check:**
1. `requirements.txt` is valid
2. Python version compatibility (Vercel uses 3.9+)
3. No syntax errors in `api/index.py`
4. View build logs in Vercel dashboard

## 🔒 Security Notes

1. **Never commit `.env` file** - Use `.vercelignore`
2. **API keys in environment variables only** - Not in code
3. **Rate limiting** - Consider adding to prevent abuse
4. **Input validation** - Already checks file size

## 🚀 Performance Tips

1. **Use CDN** - Vercel automatically uses Edge Network
2. **Optimize images** - Compress before upload
3. **Cache responses** - Add caching for repeated images (future)
4. **Choose faster model** - `claude-3-haiku` for speed

## 📊 Comparison to Other Deployments

| Platform | Setup Time | Cost | Difficulty | URL Format |
|----------|-----------|------|------------|------------|
| **Vercel** | 2 min | Free | ⭐ Easy | `app.vercel.app` |
| AWS Lambda | 15 min | $1-5 | ⭐⭐⭐ Hard | `abc.execute-api...` |
| Heroku | 10 min | $5+ | ⭐⭐ Medium | `app.herokuapp.com` |
| Render | 5 min | Free | ⭐⭐ Medium | `app.onrender.com` |

**Vercel wins for demos!** ⭐

## 📝 Customization

### Change UI Colors

Edit `public/index.html` CSS:
```css
/* Line 16: Gradient background */
background: linear-gradient(135deg, #YOUR_COLOR 0%, #YOUR_COLOR 100%);
```

### Add Your GitHub Link

Edit `public/index.html` (line ~197):
```html
<a href="https://github.com/YOURUSERNAME/pokemonDetector">
```

### Change Number of Predictions

Edit `api/index.py` (line ~179):
```python
predictions = predict_with_openrouter(image_base64, mime_type, topk=10)
```

## 🎓 Next Steps

Once deployed:

1. ✅ Add demo link to main README
2. ✅ Share on social media
3. ✅ Add to portfolio
4. ✅ Monitor usage in Vercel dashboard
5. ⭐ Star the repo!

## 🆘 Support

**Issues?**
1. Check [Vercel Status](https://vercel-status.com)
2. Check [OpenRouter Status](https://status.openrouter.ai)
3. View logs: `vercel logs`
4. Open GitHub issue

## 📚 Learn More

- [Vercel Documentation](https://vercel.com/docs)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Made with ❤️ using Vercel + OpenRouter**

Deployed in 2 minutes. Costs ~$1-5/month. Perfect for demos! 🚀
