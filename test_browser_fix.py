#!/usr/bin/env python3
"""
Test script to verify the browser fix works correctly
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_browser_installation():
    """Test browser installation and basic crawling"""
    print("🧪 Testing browser installation fix...")
    
    try:
        # Import the fixed app module
        from app import ensure_browser_installation, crawl_url
        
        # Test 1: Browser installation check
        print("\n1️⃣ Testing browser installation...")
        browser_ready = ensure_browser_installation()
        if browser_ready:
            print("✅ Browser installation check passed")
        else:
            print("❌ Browser installation check failed")
            return False
        
        # Test 2: Basic crawling
        print("\n2️⃣ Testing basic crawling...")
        result = await crawl_url(
            url="https://httpbin.org/html",
            extraction_type="markdown",
            word_count_threshold=1
        )
        
        if "error" in result:
            print(f"❌ Crawling test failed: {result['error']}")
            return False
        else:
            print("✅ Basic crawling test passed")
            print(f"   - URL: {result.get('url', 'N/A')}")
            print(f"   - Success: {result.get('success', False)}")
            print(f"   - Content length: {len(result.get('markdown', ''))}")
        
        # Test 3: Error handling
        print("\n3️⃣ Testing error handling...")
        result = await crawl_url(
            url="https://invalid-url-that-should-fail.com",
            extraction_type="markdown"
        )
        
        if "error" in result:
            print("✅ Error handling test passed (expected failure)")
        else:
            print("⚠️ Error handling test unexpected success")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_playwright_direct():
    """Test Playwright directly"""
    print("\n🎭 Testing Playwright directly...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://httpbin.org/html")
            title = page.title()
            browser.close()
            
        print(f"✅ Direct Playwright test passed - Title: {title}")
        return True
        
    except Exception as e:
        print(f"❌ Direct Playwright test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Crawl4AI Browser Fix Tests")
    print("=" * 50)
    
    # Test Playwright directly first
    playwright_ok = test_playwright_direct()
    
    # Test the application
    app_ok = await test_browser_installation()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Playwright Direct: {'✅ PASS' if playwright_ok else '❌ FAIL'}")
    print(f"   Application Tests: {'✅ PASS' if app_ok else '❌ FAIL'}")
    
    if playwright_ok and app_ok:
        print("\n🎉 All tests passed! The browser fix is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)