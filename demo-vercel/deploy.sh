#!/bin/bash
# Quick deployment script for Vercel

set -e

echo "🚀 Pokemon Detector - Vercel Deployment"
echo "========================================"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed."
    echo ""
    echo "Install it with:"
    echo "  npm install -g vercel"
    echo ""
    echo "Or use npx (no install needed):"
    echo "  npx vercel"
    exit 1
fi

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo "📝 You need to login to Vercel first"
    echo "Opening browser for login..."
    vercel login
fi

echo ""
echo "✅ Logged in to Vercel"
echo ""

# Check if OPENROUTER_API_KEY is set in environment variables
echo "🔑 Checking for OpenRouter API key..."
echo ""

if ! vercel env ls | grep -q "OPENROUTER_API_KEY"; then
    echo "⚠️  OPENROUTER_API_KEY not found in Vercel environment"
    echo ""
    read -p "Do you want to add it now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Get your API key from: https://openrouter.ai/keys"
        echo ""
        vercel env add OPENROUTER_API_KEY
    else
        echo ""
        echo "⚠️  Warning: Deployment will fail without OPENROUTER_API_KEY"
        echo "Add it later with: vercel env add OPENROUTER_API_KEY"
        echo ""
    fi
fi

echo ""
echo "🚀 Deploying to Vercel..."
echo ""

# Deploy to production
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Visit your URL (shown above)"
echo "2. Upload a Pokemon image"
echo "3. Get predictions!"
echo ""
echo "View logs with: vercel logs"
echo "View in dashboard: https://vercel.com/dashboard"
echo ""
