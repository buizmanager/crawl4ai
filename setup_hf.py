#!/usr/bin/env python3
"""
Setup script for Crawl4AI Hugging Face Spaces deployment
This script handles the installation and setup of dependencies
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    return result

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing dependencies...")
    
    # Install basic requirements
    run_command("pip install --upgrade pip")
    run_command("pip install gradio>=4.0.0")
    run_command("pip install crawl4ai[all]")
    
    # Setup Crawl4AI
    print("🚀 Setting up Crawl4AI...")
    run_command("python -m crawl4ai.install")
    
    # Install Playwright
    print("🎭 Installing Playwright...")
    run_command("playwright install chromium")
    
    print("✅ Dependencies installed successfully!")

async def test_crawl4ai():
    """Test Crawl4AI functionality"""
    print("🧪 Testing Crawl4AI...")
    
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig
        
        browser_config = BrowserConfig(
            headless=True,
            extra_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process"
            ]
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url="https://example.com")
            if result and len(result) > 0 and result[0].success:
                print("✅ Crawl4AI test successful!")
                return True
            else:
                print("❌ Crawl4AI test failed - no results")
                return False
                
    except Exception as e:
        print(f"❌ Crawl4AI test failed: {e}")
        return False

def create_hf_files():
    """Create necessary files for HF Spaces"""
    print("📝 Creating HF Spaces files...")
    
    # Create .gitignore for HF Spaces
    gitignore_content = """
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
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content.strip())
    
    print("✅ HF Spaces files created!")

def main():
    """Main setup function"""
    print("🚀 Setting up Crawl4AI for Hugging Face Spaces...")
    
    # Install dependencies
    install_dependencies()
    
    # Create HF files
    create_hf_files()
    
    # Test functionality
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(test_crawl4ai())
    loop.close()
    
    if success:
        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Copy the following files to your HF Space:")
        print("   - app.py")
        print("   - requirements_hf.txt (rename to requirements.txt)")
        print("   - README_HF.md (rename to README.md)")
        print("2. Set your Space to use Gradio SDK")
        print("3. Deploy and enjoy!")
    else:
        print("❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()