#!/usr/bin/env python3
"""
Startup script for HuggingFace Spaces to ensure Playwright browsers are properly installed
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_browser_installation():
    """Check if Playwright browsers are properly installed"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to launch browser
            browser = p.chromium.launch(headless=True)
            browser.close()
            print("✅ Playwright browser check successful")
            return True
    except Exception as e:
        print(f"❌ Playwright browser check failed: {e}")
        return False

def install_browsers():
    """Install Playwright browsers"""
    try:
        print("🔄 Installing Playwright browsers...")
        
        # Install browsers with system dependencies
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully")
            return True
        else:
            print(f"❌ Browser installation failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Browser installation timed out")
        return False
    except Exception as e:
        print(f"❌ Browser installation error: {e}")
        return False

def setup_crawl4ai():
    """Setup Crawl4AI if needed"""
    try:
        print("🔄 Setting up Crawl4AI...")
        result = subprocess.run([
            sys.executable, "-m", "crawl4ai.install"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Crawl4AI setup successful")
            return True
        else:
            print(f"⚠️ Crawl4AI setup warning: {result.stderr}")
            return True  # Continue even if setup has warnings
            
    except Exception as e:
        print(f"⚠️ Crawl4AI setup error: {e}")
        return True  # Continue even if setup fails

def main():
    """Main startup function"""
    print("🚀 Starting HuggingFace Spaces setup for Crawl4AI...")
    
    # Check if browsers are already installed
    if check_browser_installation():
        print("✅ Browsers already installed, skipping installation")
    else:
        print("🔄 Browsers not found, installing...")
        if not install_browsers():
            print("❌ Failed to install browsers, app may not work properly")
            return False
    
    # Setup Crawl4AI
    setup_crawl4ai()
    
    # Final verification
    if check_browser_installation():
        print("✅ All systems ready!")
        return True
    else:
        print("❌ Browser verification failed after installation")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("⚠️ Setup completed with warnings - some features may not work")
    sys.exit(0)  # Always exit successfully to allow app to start