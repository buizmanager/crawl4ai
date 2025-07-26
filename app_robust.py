#!/usr/bin/env python3
"""
Robust Crawl4AI Gradio Interface for Hugging Face Spaces
Falls back to simple HTTP scraping if browser automation fails
"""

import gradio as gr
import asyncio
import json
import os
import sys
import traceback
from typing import Optional, Dict, Any
import tempfile
import base64
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Handle nested event loops for Gradio
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    print("nest_asyncio not available, using standard asyncio")

# Simple HTTP-based fallback imports
import requests
from bs4 import BeautifulSoup
import html2text

# Try to import Crawl4AI with browser support
BROWSER_AVAILABLE = False
try:
    def ensure_playwright_browsers():
        """Ensure Playwright browsers are installed"""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser_path = p.chromium.executable_path
                if not os.path.exists(browser_path):
                    print("🔧 Installing Playwright browsers...")
                    os.system("playwright install chromium")
                    return True
            return True
        except Exception as e:
            print(f"⚠️ Browser setup failed: {e}")
            return False

    # Try to ensure browsers are available
    if ensure_playwright_browsers():
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        from crawl4ai.extraction_strategy import LLMExtractionStrategy
        from crawl4ai.chunking_strategy import RegexChunking
        BROWSER_AVAILABLE = True
        print("✅ Browser automation available")
    else:
        print("⚠️ Browser automation not available, using HTTP fallback")
        
except Exception as e:
    print(f"⚠️ Crawl4AI browser mode failed: {e}")
    print("📡 Using HTTP-based fallback mode")

# Thread-safe executor for running async functions
executor = ThreadPoolExecutor(max_workers=2)

def run_async_in_thread(coro):
    """Run async function in a separate thread with its own event loop"""
    def run_in_thread():
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    future = executor.submit(run_in_thread)
    return future.result(timeout=300)  # 5 minute timeout

def simple_crawl(url: str, css_selector: str = "") -> Dict[str, Any]:
    """Simple HTTP-based crawling fallback"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Set up headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else 'No title found'
        
        # Apply CSS selector if provided
        if css_selector.strip():
            selected_elements = soup.select(css_selector.strip())
            if selected_elements:
                # Create new soup with selected elements
                new_soup = BeautifulSoup('<div></div>', 'html.parser')
                for elem in selected_elements:
                    new_soup.div.append(elem)
                soup = new_soup
        
        # Convert to markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        markdown_content = h.handle(str(soup))
        
        # Extract links
        links = {'internal': [], 'external': []}
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            if href.startswith('http'):
                if url in href:
                    links['internal'].append({'href': href, 'text': text})
                else:
                    links['external'].append({'href': href, 'text': text})
            elif href.startswith('/'):
                base_url = '/'.join(url.split('/')[:3])
                full_url = base_url + href
                links['internal'].append({'href': full_url, 'text': text})
        
        # Extract media
        media = {'images': [], 'videos': []}
        for img in soup.find_all('img', src=True):
            src = img['src']
            alt = img.get('alt', '')
            if not src.startswith('http'):
                base_url = '/'.join(url.split('/')[:3])
                src = base_url + src if src.startswith('/') else url + '/' + src
            media['images'].append({'src': src, 'alt': alt})
            
        for video in soup.find_all('video', src=True):
            src = video['src']
            if not src.startswith('http'):
                base_url = '/'.join(url.split('/')[:3])
                src = base_url + src if src.startswith('/') else url + '/' + src
            media['videos'].append({'src': src})
        
        return {
            'success': True,
            'url': url,
            'title': title_text,
            'markdown': markdown_content,
            'cleaned_html': str(soup)[:5000],  # Limit size
            'links': links,
            'media': media,
            'metadata': {'method': 'HTTP + BeautifulSoup'},
            'error_message': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Simple crawl failed: {str(e)}",
            'traceback': traceback.format_exc()
        }

async def browser_crawl_async(
    url: str,
    extraction_type: str = "markdown",
    custom_prompt: str = "",
    word_count_threshold: int = 10,
    css_selector: str = "",
    screenshot: bool = False,
    pdf: bool = False
) -> Dict[str, Any]:
    """Browser-based crawling with Crawl4AI"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Create browser config optimized for HF Spaces
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
                "--single-process",  # Important for HF Spaces
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images" if not screenshot else "",  # Only load images if screenshot needed
                "--memory-pressure-off",
                "--max_old_space_size=512",  # Limit memory usage
            ]
        )
        
        # Use context manager for proper cleanup
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Configure crawler run
            config = CrawlerRunConfig(
                word_count_threshold=word_count_threshold,
                screenshot=screenshot,
                pdf=pdf,
                page_timeout=30000,  # 30 second timeout
                delay_before_return_html=2.0,  # Wait for page to load
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
                
            # Perform crawl with timeout
            result = await asyncio.wait_for(
                crawler.arun(url=url, config=config),
                timeout=120  # 2 minute timeout
            )
            
            if not result or len(result) == 0:
                return {"error": "No results returned from crawler"}
                
            crawl_result = result[0]
            
            # Prepare response
            response = {
                "success": crawl_result.success,
                "url": crawl_result.url,
                "title": getattr(crawl_result, 'title', 'N/A'),
                "markdown": crawl_result.markdown,
                "cleaned_html": crawl_result.cleaned_html[:5000] if crawl_result.cleaned_html else "",  # Limit size
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
                # Save PDF to temp file for download
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(crawl_result.pdf)
                    response["pdf_path"] = tmp.name
                    
            return response
        
    except asyncio.TimeoutError:
        return {
            "error": "Browser crawling timed out. The website may be slow or unresponsive.",
            "traceback": "TimeoutError: Operation timed out after 2 minutes"
        }
    except Exception as e:
        return {
            "error": f"Browser crawling failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

def crawl_url(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf):
    """Main crawl function with fallback logic"""
    try:
        # Try browser-based crawling first if available
        if BROWSER_AVAILABLE and not screenshot and not pdf:  # Skip browser for simple requests
            try:
                result = run_async_in_thread(
                    browser_crawl_async(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf)
                )
                if "error" not in result:
                    result["metadata"] = result.get("metadata", {})
                    result["metadata"]["method"] = "Browser (Crawl4AI)"
                    return result
                else:
                    print(f"Browser crawling failed: {result['error']}")
                    print("Falling back to simple HTTP crawling...")
            except Exception as e:
                print(f"Browser crawling exception: {e}")
                print("Falling back to simple HTTP crawling...")
        
        # Fallback to simple HTTP crawling
        result = simple_crawl(url, css_selector)
        if result.get("success"):
            return result
        else:
            return result  # Return error from simple crawl
            
    except Exception as e:
        return {
            "error": f"All crawling methods failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

def format_result(result: Dict[str, Any]) -> tuple:
    """Format the crawl result for Gradio display"""
    if "error" in result:
        error_msg = result["error"]
        if "traceback" in result:
            error_msg += f"\n\nTraceback:\n{result['traceback']}"
        return error_msg, "", "", "", None, None
    
    # Format basic info
    method = result.get('metadata', {}).get('method', 'Unknown')
    info = f"""
**URL:** {result.get('url', 'N/A')}
**Title:** {result.get('title', 'N/A')}
**Success:** {result.get('success', False)}
**Method:** {method}
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
            for link in internal_links[:10]:  # Limit to first 10
                links_info += f"- [{link.get('text', 'No text')}]({link.get('href', '#')})\n"
        
        if external_links:
            links_info += "\n**External Links:**\n"
            for link in external_links[:10]:  # Limit to first 10
                links_info += f"- [{link.get('text', 'No text')}]({link.get('href', '#')})\n"
    
    # Format media info
    media_info = ""
    if result.get('media'):
        images = result['media'].get('images', [])
        videos = result['media'].get('videos', [])
        media_info = f"**Images:** {len(images)}\n**Videos:** {len(videos)}\n"
        
        if images:
            media_info += "\n**Images:**\n"
            for img in images[:5]:  # Limit to first 5
                media_info += f"- ![{img.get('alt', 'Image')}]({img.get('src', '#')})\n"
    
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
        result = crawl_url(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf)
        return format_result(result)
    except Exception as e:
        error_msg = f"Interface error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg, "", "", "", None, None

# Create Gradio interface
def create_interface():
    browser_status = "✅ Available" if BROWSER_AVAILABLE else "❌ Not Available (using HTTP fallback)"
    
    with gr.Blocks(title="Crawl4AI - Web Crawler & Scraper", theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"""
        # 🚀🤖 Crawl4AI: Robust Web Crawler & Scraper
        
        Extract content, generate markdown, take screenshots, and more from any webpage!
        
        **Browser Automation Status:** {browser_status}
        
        **Features:**
        - 📄 Convert web pages to clean markdown
        - 🖼️ Take full-page screenshots (browser mode only)
        - 📋 Extract structured data
        - 🔗 Analyze links and media
        - 🎯 CSS selector targeting
        - 🤖 LLM-powered extraction (browser mode only)
        - 🔄 Automatic fallback to HTTP scraping
        
        **Robust Design:**
        - ✅ Automatic fallback if browser fails
        - ✅ HTTP-based scraping always works
        - ✅ Optimized for HF Spaces constraints
        - ✅ Thread-safe execution
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
                    screenshot_check = gr.Checkbox(
                        label="📸 Take Screenshot", 
                        value=False,
                        interactive=BROWSER_AVAILABLE
                    )
                    pdf_check = gr.Checkbox(
                        label="📄 Generate PDF", 
                        value=False,
                        interactive=BROWSER_AVAILABLE
                    )
                
                with gr.Accordion("⚙️ Advanced Options", open=False):
                    custom_prompt = gr.Textbox(
                        label="🤖 Custom LLM Prompt (browser mode only)",
                        placeholder="Extract all product names and prices...",
                        lines=3,
                        interactive=BROWSER_AVAILABLE
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
                gr.Markdown(f"""
                ### 💡 Tips:
                - **Markdown**: Best for general content extraction
                - **Structured**: Good for data analysis  
                - **LLM**: Use with custom prompts (browser mode only)
                - **CSS Selector**: Target specific page elements
                - **Screenshots/PDF**: Require browser mode
                
                ### 🔄 Fallback System:
                - Browser mode: Full Crawl4AI features
                - HTTP mode: Reliable BeautifulSoup scraping
                - Automatic fallback if browser fails
                
                ### ⚡ Status:
                - Browser Mode: {browser_status}
                - HTTP Fallback: ✅ Always Available
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
                ["https://example.com", "markdown", "", 10, "", False, False],
            ],
            inputs=[url_input, extraction_type, custom_prompt, word_count, css_selector, screenshot_check, pdf_check]
        )
        
        gr.Markdown("""
        ---
        **Note**: This robust version automatically falls back to HTTP scraping if browser automation fails.
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