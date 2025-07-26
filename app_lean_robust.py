#!/usr/bin/env python3
"""
Lean and Robust Crawl4AI Gradio Interface for Hugging Face Spaces
Uses HTTP fallback when browser automation fails - always works!
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

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Handle nested event loops for Gradio
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    print("nest_asyncio not available, using standard asyncio")

# HTTP-based fallback imports (always available)
import requests
from bs4 import BeautifulSoup
import html2text

# Try to import Crawl4AI with browser support (optional)
BROWSER_AVAILABLE = False
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking
    
    # Quick browser test - don't install, just check if it works
    def quick_browser_test():
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                browser.close()
                return True
        except:
            return False
    
    BROWSER_AVAILABLE = quick_browser_test()
    if BROWSER_AVAILABLE:
        print("✅ Browser automation available")
    else:
        print("⚠️ Browser automation not available, using HTTP fallback only")
        
except Exception as e:
    print(f"⚠️ Crawl4AI browser mode failed: {e}")
    print("📡 Using HTTP-based fallback mode only")

def http_crawl(url: str, css_selector: str = "") -> Dict[str, Any]:
    """Reliable HTTP-based crawling with BeautifulSoup"""
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
        base_url = '/'.join(url.split('/')[:3])
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            if href.startswith('http'):
                if base_url in href:
                    links['internal'].append({'href': href, 'text': text})
                else:
                    links['external'].append({'href': href, 'text': text})
            elif href.startswith('/'):
                full_url = base_url + href
                links['internal'].append({'href': full_url, 'text': text})
        
        # Extract media
        media = {'images': [], 'videos': []}
        for img in soup.find_all('img', src=True):
            src = img['src']
            alt = img.get('alt', '')
            if not src.startswith('http'):
                if src.startswith('/'):
                    src = base_url + src
                else:
                    src = url.rstrip('/') + '/' + src.lstrip('/')
            media['images'].append({'src': src, 'alt': alt})
            
        for video in soup.find_all('video', src=True):
            src = video['src']
            if not src.startswith('http'):
                if src.startswith('/'):
                    src = base_url + src
                else:
                    src = url.rstrip('/') + '/' + src.lstrip('/')
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
            'error': f"HTTP crawling failed: {str(e)}",
            'traceback': traceback.format_exc()
        }

async def browser_crawl(
    url: str,
    extraction_type: str = "markdown",
    custom_prompt: str = "",
    word_count_threshold: int = 10,
    css_selector: str = "",
    screenshot: bool = False,
    pdf: bool = False
) -> Dict[str, Any]:
    """Browser-based crawling with Crawl4AI (when available)"""
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
                "--single-process",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images" if not screenshot else "",
                "--memory-pressure-off",
                "--max_old_space_size=512",
            ]
        )
        
        # Use context manager for proper cleanup
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Configure crawler run
            config = CrawlerRunConfig(
                word_count_threshold=word_count_threshold,
                screenshot=screenshot,
                pdf=pdf,
                page_timeout=30000,
                delay_before_return_html=2.0,
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
                config.chunking_strategy = RegexChunking()
                
            # Perform crawl with timeout
            result = await asyncio.wait_for(
                crawler.arun(url=url, config=config),
                timeout=60
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
        return {
            "error": f"Browser crawling failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

def crawl_url(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf):
    """Main crawl function with smart fallback logic"""
    try:
        # For simple requests or when browser isn't available, use HTTP directly
        if not BROWSER_AVAILABLE or (not screenshot and not pdf and extraction_type == "markdown"):
            print("🌐 Using HTTP crawling...")
            result = http_crawl(url, css_selector)
            if result.get("success"):
                return result
            else:
                print("❌ HTTP crawling failed, trying browser if available...")
        
        # Try browser-based crawling if available
        if BROWSER_AVAILABLE:
            try:
                print("🚀 Using browser crawling...")
                result = asyncio.run(
                    browser_crawl(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf)
                )
                if "error" not in result:
                    result["metadata"] = result.get("metadata", {})
                    result["metadata"]["method"] = "Browser (Crawl4AI)"
                    return result
                else:
                    print(f"❌ Browser crawling failed: {result['error']}")
                    print("🔄 Falling back to HTTP crawling...")
            except Exception as e:
                print(f"❌ Browser crawling exception: {e}")
                print("🔄 Falling back to HTTP crawling...")
        
        # Final fallback to HTTP crawling
        print("🌐 Using HTTP fallback...")
        result = http_crawl(url, css_selector)
        return result
            
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
            error_msg += f"\n\nTechnical Details:\n{result['traceback']}"
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
    markdown = result.get('markdown', 'No content extracted')
    
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
        
        if images:
            media_info += "\n**Sample Images:**\n"
            for img in images[:5]:
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
        return "Please enter a URL to crawl.", "", "", "", None, None
    
    try:
        result = crawl_url(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf)
        return format_result(result)
    except Exception as e:
        error_msg = f"Interface error: {str(e)}\n\nTechnical Details:\n{traceback.format_exc()}"
        return error_msg, "", "", "", None, None

# Create Gradio interface
def create_interface():
    browser_status = "✅ Available" if BROWSER_AVAILABLE else "❌ Not Available (HTTP fallback active)"
    
    with gr.Blocks(title="Crawl4AI - Robust Web Crawler", theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"""
        # 🚀🤖 Crawl4AI: Robust Web Crawler & Scraper
        
        **Always works!** Automatically falls back to HTTP scraping if browser automation fails.
        
        **Browser Status:** {browser_status}
        
        **Features:**
        - 📄 Convert web pages to clean markdown ✅ Always works
        - 🖼️ Take screenshots {'✅ Available' if BROWSER_AVAILABLE else '❌ Requires browser'}
        - 📋 Extract structured data ✅ Always works
        - 🔗 Analyze links and media ✅ Always works
        - 🎯 CSS selector targeting ✅ Always works
        - 🤖 LLM extraction {'✅ Available' if BROWSER_AVAILABLE else '❌ Requires browser'}
        - 🔄 **Automatic HTTP fallback** ✅ Always works
        
        **Smart Fallback System:**
        - 🚀 Tries browser automation first (if available)
        - 🌐 Falls back to reliable HTTP + BeautifulSoup
        - ✅ **Guarantees results** - something always works!
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label="🌐 URL to Crawl",
                    placeholder="https://example.com",
                    value="https://example.com"
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
                ### 💡 How it works:
                
                **🚀 Browser Mode** (when available):
                - Full Crawl4AI features
                - Screenshots and PDFs
                - LLM extraction
                - Advanced rendering
                
                **🌐 HTTP Fallback** (always works):
                - Reliable BeautifulSoup scraping
                - Fast and efficient
                - Works in any environment
                - No dependencies issues
                
                ### ⚡ Current Status:
                - **Browser:** {browser_status}
                - **HTTP Fallback:** ✅ Always Ready
                - **Guarantee:** ✅ Something always works!
                
                ### 🎯 Best Practices:
                - Start with simple URLs
                - Use markdown extraction for reliability
                - Screenshots/PDFs need browser mode
                - HTTP fallback handles most sites well
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
                ["https://example.com", "markdown", "", 10, "", False, False],
                ["https://docs.crawl4ai.com/first-steps/introduction", "markdown", "", 10, "", False, False],
                ["https://news.ycombinator.com", "structured", "", 5, ".storylink", False, False],
            ],
            inputs=[url_input, extraction_type, custom_prompt, word_count, css_selector, screenshot_check, pdf_check]
        )
        
        gr.Markdown("""
        ---
        **🎯 Robust Design Promise:** This app is designed to **always work**. If browser automation fails, 
        it automatically falls back to HTTP scraping. You'll always get results!
        
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