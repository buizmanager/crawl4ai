#!/usr/bin/env python3
"""
Startup script for Crawl4AI HF Spaces deployment
Ensures all dependencies are properly installed before starting the app
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Run a shell command and return the result"""
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)
    if check and result.returncode != 0:
        print(f"❌ Error running command: {cmd}")
        if capture_output:
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
        return False
    return True

def check_playwright_browsers():
    """Check if Playwright browsers are installed"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to get browser path
            browser_path = p.chromium.executable_path
            if browser_path and Path(browser_path).exists():
                print(f"✅ Chromium browser found at: {browser_path}")
                return True
            else:
                print(f"❌ Chromium browser not found at: {browser_path}")
                return False
    except Exception as e:
        print(f"❌ Error checking Playwright browsers: {e}")
        return False

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("📦 Installing Playwright browsers...")
    
    # Install browsers
    if not run_command("playwright install chromium", capture_output=False):
        print("❌ Failed to install Playwright browsers")
        return False
    
    # Install system dependencies
    if not run_command("playwright install-deps chromium", capture_output=False):
        print("⚠️ Warning: Failed to install system dependencies (may not be needed)")
    
    return True

def test_browser():
    """Test if browser can be launched"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://example.com")
            title = page.title()
            browser.close()
            print(f"✅ Browser test successful! Page title: {title}")
            return True
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        return False

async def test_crawl4ai():
    """Test Crawl4AI functionality"""
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

def main():
    """Main startup function"""
    print("🚀 Starting Crawl4AI HF Spaces setup...")
    
    # Check if browsers are installed
    if not check_playwright_browsers():
        print("📦 Playwright browsers not found, installing...")
        if not install_playwright_browsers():
            print("❌ Failed to install browsers, trying to continue anyway...")
        else:
            print("✅ Browsers installed successfully!")
    
    # Test browser functionality
    if not test_browser():
        print("❌ Browser test failed, but continuing...")
    
    # Test Crawl4AI
    print("🧪 Testing Crawl4AI...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(test_crawl4ai())
    loop.close()
    
    if success:
        print("🎉 All tests passed! Starting the application...")
    else:
        print("⚠️ Some tests failed, but starting the application anyway...")
    
    # Start the main application
    print("🚀 Launching Gradio interface...")
    
    # Import and run the main app
    try:
        if os.path.exists("app_fixed.py"):
            print("Using app_fixed.py")
            import app_fixed
            demo = app_fixed.create_interface()
        else:
            print("Using app.py")
            import app
            demo = app.create_interface()
            
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()