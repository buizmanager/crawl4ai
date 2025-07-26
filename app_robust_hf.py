#!/usr/bin/env python3
"""
Crawl4AI Gradio Interface for Hugging Face Spaces - Robust Version
This version handles browser installation issues more gracefully
"""

import gradio as gr
import asyncio
import json
import os
import sys
import traceback
import subprocess
from typing import Optional, Dict, Any
import tempfile
import base64

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Handle nested event loops for Gradio
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    print("nest_asyncio not available, using standard asyncio")

def check_browser_availability():
    """Check if Playwright browsers are available without trying to install"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
            return True
    except Exception as e:
        print(f"Browser check failed: {e}")
        return False

def try_install_browsers():
    """Try to install browsers without system dependencies"""
    try:
        print("🔄 Attempting to install Playwright browsers...")
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Browser installation completed")
            return check_browser_availability()
        else:
            print(f"⚠️ Browser installation had issues: {result.stderr}")
            return check_browser_availability()
    except Exception as e:
        print(f"⚠️ Browser installation failed: {e}")
        return False

# Check browser availability at startup
print("🔄 Checking browser availability...")
browser_ready = check_browser_availability()

if not browser_ready:
    print("🔄 Browsers not ready, attempting installation...")
    browser_ready = try_install_browsers()

if browser_ready:
    print("✅ Browsers are ready!")
else:
    print("⚠️ Browsers are not available - some features may not work")

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking
    from crawl4ai.content_filter_strategy import BM25ContentFilter
except ImportError as e:
    print(f"Import error: {e}")
    print("Installing crawl4ai...")
    os.system("pip install crawl4ai")
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking
    from crawl4ai.content_filter_strategy import BM25ContentFilter

async def crawl_url(
    url: str,
    extraction_type: str = "markdown",
    custom_prompt: str = "",
    word_count_threshold: int = 10,
    css_selector: str = "",
    screenshot: bool = False,
    pdf: bool = False
) -> Dict[str, Any]:
    """
    Crawl a single URL and return results
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Check browser availability
        if not browser_ready:
            # Try one more time to install browsers
            print("🔄 Final attempt to install browsers...")
            if not try_install_browsers():
                return {
                    "error": "Browser installation failed. This appears to be a system-level issue in the HuggingFace Spaces environment. Please try:\n\n1. Refreshing the page\n2. Trying again in a few minutes\n3. Using a simpler URL\n\nIf the problem persists, this may be due to system restrictions in the current environment.",
                    "traceback": "Playwright browsers could not be installed or launched. This is likely due to missing system dependencies or permission restrictions in the containerized environment."
                }
        
        # Create browser configuration with extensive compatibility flags
        browser_config = BrowserConfig(
            headless=True,
            text_mode=True,
            extra_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage", 
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-web-security",
                "--allow-insecure-localhost",
                "--ignore-certificate-errors",
                "--single-process",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--metrics-recording-only",
                "--no-first-run",
                "--disable-ipc-flooding-protection",
                "--disable-hang-monitor",
                "--disable-prompt-on-repost",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--disable-domain-reliability",
            ]
        )
        
        # Use context manager for proper cleanup
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Configure crawler run
            config = CrawlerRunConfig(
                word_count_threshold=word_count_threshold,
                screenshot=screenshot,
                pdf=pdf
            )
            
            # Add CSS selector if provided
            if css_selector.strip():
                config.css_selector = css_selector.strip()
                
            # Add extraction strategy if needed
            if extraction_type == "llm" and custom_prompt.strip():
                config.extraction_strategy = LLMExtractionStrategy(
                    provider="openai/gpt-4o-mini",
                    api_token=os.getenv("OPENAI_API_KEY", ""),
                    instruction=custom_prompt
                )
            elif extraction_type == "structured":
                # Use regex chunking for structured extraction
                config.chunking_strategy = RegexChunking()
                
            # Perform crawl
            result = await crawler.arun(url=url, config=config)
            
            if not result or len(result) == 0:
                return {"error": "No results returned from crawler"}
                
            crawl_result = result[0]
            
            # Prepare response
            response = {
                "success": crawl_result.success,
                "url": crawl_result.url,
                "title": getattr(crawl_result, 'title', 'N/A'),
                "markdown": crawl_result.markdown,
                "cleaned_html": crawl_result.cleaned_html[:5000] if crawl_result.cleaned_html else "",
                "links": crawl_result.links,
                "media": crawl_result.media,
                "metadata": crawl_result.metadata,
                "error_message": crawl_result.error_message
            }
            
            # Add extraction results if available
            if hasattr(crawl_result, 'extracted_content') and crawl_result.extracted_content:
                response["extracted_content"] = crawl_result.extracted_content
                
            # Handle screenshot
            if screenshot and crawl_result.screenshot:
                response["screenshot"] = crawl_result.screenshot
                
            # Handle PDF
            if pdf and crawl_result.pdf:
                response["pdf_size"] = len(crawl_result.pdf)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(crawl_result.pdf)
                    response["pdf_path"] = tmp.name
                    
            return response
        
    except Exception as e:
        error_msg = str(e)
        if "BrowserType.launch" in error_msg or "Executable doesn't exist" in error_msg:
            return {
                "error": "Browser launch failed. This is a known issue in some HuggingFace Spaces environments. Please try:\n\n1. Refreshing the page and trying again\n2. Using a different URL\n3. Waiting a moment and retrying\n\nThe system is attempting to recover automatically.",
                "traceback": f"Browser launch error: {error_msg}"
            }
        else:
            return {
                "error": f"Crawling failed: {error_msg}",
                "traceback": traceback.format_exc()
            }

def format_result(result: Dict[str, Any]) -> tuple:
    """Format the crawl result for Gradio display"""
    if "error" in result:
        error_msg = result["error"]
        if "traceback" in result:
            error_msg += f"\n\nTechnical Details:\n{result['traceback']}"
        return error_msg, "", "", "", None, None
    
    # Format basic info
    info = f"""
**URL:** {result.get('url', 'N/A')}
**Title:** {result.get('title', 'N/A')}
**Success:** {result.get('success', False)}
**Error:** {result.get('error_message', 'None')}
"""
    
    # Get markdown content
    markdown = result.get('markdown', '')
    
    # Format links
    links_info = ""
    if result.get('links'):
        internal_links = result['links'].get('internal', [])
        external_links = result['links'].get('external', [])
        links_info = f"**Internal Links:** {len(internal_links)}\n**External Links:** {len(external_links)}\n\n"
        
        if internal_links:
            links_info += "**Internal Links:**\n"
            for link in internal_links[:10]:
                links_info += f"- [{link.get('text', 'No text')}]({link.get('href', '#')})\n"
        
        if external_links:
            links_info += "\n**External Links:**\n"
            for link in external_links[:10]:
                links_info += f"- [{link.get('text', 'No text')}]({link.get('href', '#')})\n"
    
    # Format media info
    media_info = ""
    if result.get('media'):
        images = result['media'].get('images', [])
        videos = result['media'].get('videos', [])
        media_info = f"**Images:** {len(images)}\n**Videos:** {len(videos)}\n"
    
    # Handle screenshot
    screenshot_file = None
    if result.get('screenshot'):
        try:
            screenshot_data = base64.b64decode(result['screenshot'])
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp.write(screenshot_data)
                screenshot_file = tmp.name
        except Exception as e:
            print(f"Screenshot processing error: {e}")
    
    # Handle PDF
    pdf_file = None
    if result.get('pdf_path'):
        pdf_file = result['pdf_path']
    
    return info, markdown, links_info, media_info, screenshot_file, pdf_file

def crawl_interface(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf):
    """Gradio interface function"""
    if not url.strip():
        return "Please enter a URL", "", "", "", None, None
    
    try:
        result = asyncio.run(
            crawl_url(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf)
        )
        
        return format_result(result)
    except Exception as e:
        error_msg = f"Interface error: {str(e)}\n\nTechnical Details:\n{traceback.format_exc()}"
        return error_msg, "", "", "", None, None

# Create Gradio interface
def create_interface():
    with gr.Blocks(title="Crawl4AI - Web Crawler & Scraper", theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"""
        # 🚀🤖 Crawl4AI: Web Crawler & Scraper
        
        Extract content, generate markdown, take screenshots, and more from any webpage!
        
        **Status:** {'✅ Browsers Ready' if browser_ready else '⚠️ Browser Issues Detected - Some features may not work'}
        
        **Features:**
        - 📄 Convert web pages to clean markdown
        - 🖼️ Take full-page screenshots  
        - 📋 Extract structured data
        - 🔗 Analyze links and media
        - 🎯 CSS selector targeting
        - 🤖 LLM-powered extraction
        """)
        
        if not browser_ready:
            gr.Markdown("""
            ⚠️ **Notice:** Browser installation issues detected. The system will attempt to recover automatically.
            If you encounter errors, try refreshing the page or using simpler URLs.
            """)
        
        with gr.Row():
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label="🌐 URL to Crawl",
                    placeholder="https://example.com",
                    value="https://docs.crawl4ai.com/first-steps/introduction"
                )
                
                with gr.Row():
                    extraction_type = gr.Radio(
                        choices=["markdown", "structured", "llm"],
                        value="markdown",
                        label="📊 Extraction Type"
                    )
                    
                with gr.Row():
                    screenshot_check = gr.Checkbox(label="📸 Take Screenshot", value=False)
                    pdf_check = gr.Checkbox(label="📄 Generate PDF", value=False)
                
                with gr.Accordion("⚙️ Advanced Options", open=False):
                    custom_prompt = gr.Textbox(
                        label="🤖 Custom LLM Prompt (for LLM extraction)",
                        placeholder="Extract all product names and prices...",
                        lines=3
                    )
                    
                    word_count = gr.Slider(
                        minimum=1,
                        maximum=100,
                        value=10,
                        step=1,
                        label="📝 Word Count Threshold"
                    )
                    
                    css_selector = gr.Textbox(
                        label="🎯 CSS Selector (optional)",
                        placeholder="article, .content, #main"
                    )
                
                crawl_btn = gr.Button("🚀 Crawl Website", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("""
                ### 💡 Tips:
                - **Markdown**: Best for general content extraction
                - **Structured**: Good for data analysis  
                - **LLM**: Use with custom prompts for specific extraction
                - **CSS Selector**: Target specific page elements
                - **Screenshots**: Capture visual content
                
                ### 🔧 Troubleshooting:
                - If you get browser errors, try refreshing the page
                - Start with simple URLs like example.com
                - Disable screenshots/PDFs if having issues
                """)
        
        # Output sections
        with gr.Row():
            with gr.Column():
                info_output = gr.Markdown(label="ℹ️ Page Information")
                
        with gr.Tabs():
            with gr.TabItem("📝 Markdown Content"):
                markdown_output = gr.Textbox(
                    label="Extracted Markdown",
                    lines=20,
                    max_lines=30,
                    show_copy_button=True
                )
            
            with gr.TabItem("🔗 Links Analysis"):
                links_output = gr.Markdown(label="Links Found")
                
            with gr.TabItem("🖼️ Media Info"):
                media_output = gr.Markdown(label="Media Elements")
                
            with gr.TabItem("📸 Screenshot"):
                screenshot_output = gr.Image(label="Page Screenshot", type="filepath")
                
            with gr.TabItem("📄 PDF"):
                pdf_output = gr.File(label="Generated PDF")
        
        # Connect the interface
        crawl_btn.click(
            fn=crawl_interface,
            inputs=[
                url_input, extraction_type, custom_prompt, 
                word_count, css_selector, screenshot_check, pdf_check
            ],
            outputs=[
                info_output, markdown_output, links_output, 
                media_output, screenshot_output, pdf_output
            ]
        )
        
        # Examples
        gr.Examples(
            examples=[
                ["https://docs.crawl4ai.com/first-steps/introduction", "markdown", "", 10, "", False, False],
                ["https://news.ycombinator.com", "structured", "", 5, ".storylink", False, False],
                ["https://example.com", "llm", "Extract the main heading and description", 10, "", False, False],
            ],
            inputs=[url_input, extraction_type, custom_prompt, word_count, css_selector, screenshot_check, pdf_check]
        )
        
        gr.Markdown("""
        ---
        **Note**: This is a simplified version of Crawl4AI optimized for Hugging Face Spaces. 
        For full features and API access, visit the [Crawl4AI GitHub repository](https://github.com/unclecode/crawl4ai).
        """)
    
    return demo

# Create and launch the interface
if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )