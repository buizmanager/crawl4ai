#!/usr/bin/env python3
"""
Crawl4AI Gradio Interface for Hugging Face Spaces - Final Robust Version
This version assumes browsers are pre-installed and focuses on graceful error handling
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

def check_browser_status():
    """Check browser status without attempting installation"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to launch browser with minimal configuration
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process"
                ]
            )
            browser.close()
            return True, "✅ Browsers are ready"
    except Exception as e:
        return False, f"❌ Browser check failed: {str(e)}"

# Check browser status at startup
browser_ready, browser_status = check_browser_status()
print(f"Browser Status: {browser_status}")

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking
    from crawl4ai.content_filter_strategy import BM25ContentFilter
    print("✅ Crawl4AI imported successfully")
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
        
        # If browsers aren't ready, return helpful error
        if not browser_ready:
            return {
                "error": "Browser system is not available in this environment. This may be due to:\n\n" +
                        "• System dependency issues in the container\n" +
                        "• Resource constraints in HuggingFace Spaces\n" +
                        "• Browser installation problems\n\n" +
                        "Please try:\n" +
                        "1. Refreshing the page and waiting a moment\n" +
                        "2. Trying again in a few minutes\n" +
                        "3. Using a different deployment method\n\n" +
                        "For full functionality, consider running Crawl4AI locally or on a dedicated server.",
                "traceback": f"Browser status check failed: {browser_status}"
            }
        
        # Create browser configuration optimized for HF Spaces
        browser_config = BrowserConfig(
            headless=True,
            text_mode=True,
            extra_args=[
                # Essential flags for containerized environments
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--single-process",
                
                # Security and stability flags
                "--disable-web-security",
                "--allow-insecure-localhost",
                "--ignore-certificate-errors",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                
                # Performance optimizations
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
                "--disable-hang-monitor",
                "--disable-prompt-on-repost",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--disable-domain-reliability",
                
                # Memory optimizations
                "--memory-pressure-off",
                "--max_old_space_size=4096",
                "--disable-background-mode",
            ]
        )
        
        # Use context manager for proper cleanup
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Configure crawler run
            config = CrawlerRunConfig(
                word_count_threshold=word_count_threshold,
                screenshot=screenshot and browser_ready,  # Only if browsers work
                pdf=pdf and browser_ready  # Only if browsers work
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
            try:
                result = await asyncio.wait_for(
                    crawler.arun(url=url, config=config),
                    timeout=60.0  # 60 second timeout
                )
            except asyncio.TimeoutError:
                return {
                    "error": "Crawling timed out after 60 seconds. The website may be slow or unresponsive. Please try:\n\n" +
                            "• A different URL\n" +
                            "• Disabling screenshots/PDF generation\n" +
                            "• Using a simpler extraction method",
                    "traceback": "Crawling operation timed out"
                }
            
            if not result or len(result) == 0:
                return {
                    "error": "No results returned from crawler. This could be due to:\n\n" +
                            "• The website blocking automated access\n" +
                            "• Network connectivity issues\n" +
                            "• Invalid URL format\n\n" +
                            "Please verify the URL and try again.",
                    "traceback": "Empty result set returned from crawler"
                }
                
            crawl_result = result[0]
            
            # Check if crawling was successful
            if not crawl_result.success:
                error_msg = crawl_result.error_message or "Unknown crawling error"
                return {
                    "error": f"Crawling failed: {error_msg}\n\nThis could be due to:\n" +
                            "• Website access restrictions\n" +
                            "• Invalid URL or server issues\n" +
                            "• Network connectivity problems\n\n" +
                            "Please try a different URL or check if the website is accessible.",
                    "traceback": f"Crawler reported failure: {error_msg}"
                }
            
            # Prepare response
            response = {
                "success": crawl_result.success,
                "url": crawl_result.url,
                "title": getattr(crawl_result, 'title', 'N/A'),
                "markdown": crawl_result.markdown or "No content extracted",
                "cleaned_html": (crawl_result.cleaned_html[:5000] if crawl_result.cleaned_html else ""),
                "links": crawl_result.links or {},
                "media": crawl_result.media or {},
                "metadata": crawl_result.metadata or {},
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
        
        # Provide specific error handling for common issues
        if "BrowserType.launch" in error_msg or "Executable doesn't exist" in error_msg:
            return {
                "error": "Browser launch failed. This is a system-level issue in the current environment.\n\n" +
                        "Possible causes:\n" +
                        "• Missing browser dependencies\n" +
                        "• Insufficient system resources\n" +
                        "• Container environment restrictions\n\n" +
                        "Solutions:\n" +
                        "1. Try refreshing the page\n" +
                        "2. Wait a few minutes and try again\n" +
                        "3. Use a simpler URL (like example.com)\n" +
                        "4. Disable screenshots and PDF generation\n\n" +
                        "For consistent results, consider running Crawl4AI locally.",
                "traceback": f"Browser launch error: {error_msg}"
            }
        elif "TimeoutError" in error_msg or "timeout" in error_msg.lower():
            return {
                "error": "Operation timed out. The website may be slow or the request is taking too long.\n\n" +
                        "Please try:\n" +
                        "• A faster-loading website\n" +
                        "• Disabling screenshots/PDF generation\n" +
                        "• Using a simpler extraction method",
                "traceback": f"Timeout error: {error_msg}"
            }
        elif "ConnectionError" in error_msg or "connection" in error_msg.lower():
            return {
                "error": "Network connection failed. This could be due to:\n\n" +
                        "• Website is down or unreachable\n" +
                        "• Network connectivity issues\n" +
                        "• Firewall or security restrictions\n\n" +
                        "Please verify the URL and try again.",
                "traceback": f"Connection error: {error_msg}"
            }
        else:
            return {
                "error": f"Crawling failed with error: {error_msg}\n\n" +
                        "This is an unexpected error. Please try:\n" +
                        "• Using a different URL\n" +
                        "• Simplifying your request\n" +
                        "• Refreshing the page\n\n" +
                        "If the problem persists, there may be a system issue.",
                "traceback": traceback.format_exc()
            }

def format_result(result: Dict[str, Any]) -> tuple:
    """Format the crawl result for Gradio display"""
    if "error" in result:
        error_msg = result["error"]
        if "traceback" in result:
            error_msg += f"\n\n--- Technical Details ---\n{result['traceback']}"
        return error_msg, "", "", "", None, None
    
    # Format basic info
    info = f"""
**URL:** {result.get('url', 'N/A')}
**Title:** {result.get('title', 'N/A')}
**Success:** {result.get('success', False)}
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
        result = asyncio.run(
            crawl_url(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf)
        )
        
        return format_result(result)
    except Exception as e:
        error_msg = f"Interface error: {str(e)}\n\n--- Technical Details ---\n{traceback.format_exc()}"
        return error_msg, "", "", "", None, None

# Create Gradio interface
def create_interface():
    with gr.Blocks(title="Crawl4AI - Web Crawler & Scraper", theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"""
        # 🚀🤖 Crawl4AI: Web Crawler & Scraper
        
        Extract content, generate markdown, take screenshots, and more from any webpage!
        
        **System Status:** {browser_status}
        
        **Features:**
        - 📄 Convert web pages to clean markdown
        - 🖼️ Take full-page screenshots {'✅' if browser_ready else '❌ (Unavailable)'}
        - 📋 Extract structured data
        - 🔗 Analyze links and media
        - 🎯 CSS selector targeting
        - 🤖 LLM-powered extraction
        """)
        
        if not browser_ready:
            gr.Markdown("""
            ⚠️ **System Notice:** Browser functionality is currently limited due to environment constraints.
            Basic text extraction should still work, but screenshots and PDF generation may not be available.
            
            **Troubleshooting Tips:**
            - Try refreshing the page
            - Use simple URLs like `example.com`
            - Disable screenshots and PDF generation
            - Focus on text extraction features
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
                        interactive=browser_ready
                    )
                    pdf_check = gr.Checkbox(
                        label="📄 Generate PDF", 
                        value=False,
                        interactive=browser_ready
                    )
                
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
                
                ### 🔧 Troubleshooting:
                - Start with simple URLs (example.com)
                - Disable screenshots/PDFs if having issues
                - Try refreshing if you get errors
                - Use markdown extraction for best results
                
                ### ✅ Recommended Test URLs:
                - https://example.com
                - https://httpbin.org/html
                - https://docs.crawl4ai.com
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
        
        # Examples - use simple URLs that are likely to work
        gr.Examples(
            examples=[
                ["https://example.com", "markdown", "", 10, "", False, False],
                ["https://httpbin.org/html", "markdown", "", 5, "", False, False],
                ["https://docs.crawl4ai.com/first-steps/introduction", "structured", "", 10, "", False, False],
            ],
            inputs=[url_input, extraction_type, custom_prompt, word_count, css_selector, screenshot_check, pdf_check]
        )
        
        gr.Markdown("""
        ---
        **Note**: This is a simplified version of Crawl4AI optimized for Hugging Face Spaces constraints. 
        For full features and API access, visit the [Crawl4AI GitHub repository](https://github.com/unclecode/crawl4ai).
        
        **Having Issues?** Try these steps:
        1. Use simple URLs like `example.com` first
        2. Disable screenshots and PDF generation
        3. Refresh the page if you encounter errors
        4. Focus on markdown extraction for best results
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