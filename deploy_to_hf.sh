#!/bin/bash

# Crawl4AI Hugging Face Spaces Deployment Script
# This script helps you deploy Crawl4AI to HF Spaces

set -e

echo "🚀 Crawl4AI Hugging Face Spaces Deployment Helper"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "app_simple.py" ]; then
    echo "❌ Error: app_simple.py not found. Please run this script from the crawl4ai directory."
    exit 1
fi

# Ask user for deployment type
echo ""
echo "Choose deployment type:"
echo "1) Simple Version (Recommended - reliable, fast)"
echo "2) Full Version (Advanced - more features, higher resource usage)"
echo ""
read -p "Enter choice (1 or 2): " choice

# Ask for HF Space details
echo ""
read -p "Enter your HuggingFace username: " hf_username
read -p "Enter your space name: " space_name

# Create deployment directory
deploy_dir="hf_space_${space_name}"
echo ""
echo "📁 Creating deployment directory: $deploy_dir"
mkdir -p "$deploy_dir"

# Copy files based on choice
if [ "$choice" = "1" ]; then
    echo "📦 Preparing Simple Version files..."
    cp app_simple.py "$deploy_dir/app.py"
    cp requirements_simple.txt "$deploy_dir/requirements.txt"
    
    # Create README with proper header
    cat > "$deploy_dir/README.md" << EOF
---
title: $space_name
emoji: 🚀🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Crawl4AI Simple Web Scraper - Extract content from any webpage
---

$(cat README_HF.md | tail -n +12)
EOF

elif [ "$choice" = "2" ]; then
    echo "📦 Preparing Full Version files..."
    cp app.py "$deploy_dir/app.py"
    cp requirements_hf.txt "$deploy_dir/requirements.txt"
    cp Dockerfile.hf "$deploy_dir/Dockerfile"
    
    # Create README with proper header
    cat > "$deploy_dir/README.md" << EOF
---
title: $space_name
emoji: 🚀🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Crawl4AI Full Web Crawler - Advanced web scraping with browser automation
---

$(cat README_HF.md | tail -n +12)
EOF

else
    echo "❌ Invalid choice. Exiting."
    exit 1
fi

# Create .gitignore
cat > "$deploy_dir/.gitignore" << EOF
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.DS_Store
*.log
temp/
tmp/
EOF

echo "✅ Files prepared successfully!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. Create your HF Space:"
echo "   → Go to: https://huggingface.co/new-space"
echo "   → Name: $space_name"
echo "   → SDK: Gradio"
echo "   → Visibility: Public (or Private)"
echo ""
echo "2. Clone your space repository:"
echo "   git clone https://huggingface.co/spaces/$hf_username/$space_name"
echo "   cd $space_name"
echo ""
echo "3. Copy the prepared files:"
echo "   cp ../$deploy_dir/* ."
echo "   cp ../$deploy_dir/.gitignore ."
echo ""
echo "4. Deploy to HF Spaces:"
echo "   git add ."
echo "   git commit -m \"Deploy Crawl4AI to HF Spaces\""
echo "   git push"
echo ""
echo "5. Monitor your deployment:"
echo "   → Visit: https://huggingface.co/spaces/$hf_username/$space_name"
echo "   → Check the 'Logs' tab for build progress"
echo "   → Wait for build to complete (2-10 minutes)"
echo ""

if [ "$choice" = "1" ]; then
    echo "🎯 Simple Version Tips:"
    echo "- Build time: ~2 minutes"
    echo "- Memory usage: ~500MB"
    echo "- Success rate: 95%+"
    echo "- Perfect for most use cases"
else
    echo "⚠️  Full Version Tips:"
    echo "- Build time: ~5-10 minutes"
    echo "- Memory usage: ~2GB+"
    echo "- May need GPU upgrade for stability"
    echo "- Monitor logs carefully"
fi

echo ""
echo "📚 Need help? Check DEPLOY_HF.md for detailed instructions!"
echo ""
echo "🎉 Happy scraping! Your files are ready in: $deploy_dir/"