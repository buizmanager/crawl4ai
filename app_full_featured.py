#!/usr/bin/env python3
"""
Full-Featured Crawl4AI Gradio Interface for Hugging Face Spaces
Includes all advertised functionality with robust HTTP fallback
"""

import gradio as gr
import asyncio
import json
import os
import sys
import traceback
from typing import Optional, Dict, Any, List
import tempfile
import base64
import time
from datetime import datetime

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

# Try to import Crawl4AI with full functionality
BROWSER_AVAILABLE = False
CRAWL4AI_AVAILABLE = False

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy, RegexExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking, NlpSentenceChunking, FixedLengthWordChunking
    from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter
    from crawl4ai.cache_context import CacheMode
    CRAWL4AI_AVAILABLE = True
    
    # Quick browser test - don't install, just check if it works
    def quick_browser_test():
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True, 
                    args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process"]
                )
                browser.close()
                return True
        except Exception as e:
            print(f"Browser test failed: {e}")
            return False
    
    BROWSER_AVAILABLE = quick_browser_test()
    if BROWSER_AVAILABLE:
        print("✅ Full Crawl4AI with browser automation available")
    else:
        print("⚠️ Crawl4AI available but browser automation failed, using HTTP fallback")
        
except Exception as e:
    print(f"⚠️ Crawl4AI import failed: {e}")
    print("📡 Using HTTP-based fallback mode only")

def http_crawl(url: str, css_selector: str = "", word_count_threshold: int = 10) -> Dict[str, Any]:
    """Enhanced HTTP-based crawling with BeautifulSoup"""
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
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "aside"]):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else 'No title found'
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''
        
        # Apply CSS selector if provided
        if css_selector.strip():
            selected_elements = soup.select(css_selector.strip())
            if selected_elements:
                # Create new soup with selected elements
                new_soup = BeautifulSoup('<div></div>', 'html.parser')
                for elem in selected_elements:
                    new_soup.div.append(elem)
                soup = new_soup
        
        # Convert to markdown with better formatting
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0
        h.unicode_snob = True
        h.mark_code = True
        markdown_content = h.handle(str(soup))
        
        # Apply word count threshold
        words = markdown_content.split()
        if len(words) < word_count_threshold:
            markdown_content = f"Content too short ({len(words)} words, threshold: {word_count_threshold})\n\n{markdown_content}"
        
        # Extract links with better categorization
        links = {'internal': [], 'external': []}
        base_url = '/'.join(url.split('/')[:3])
        domain = url.split('/')[2]
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            if not text:
                text = href
            
            if href.startswith('http'):
                if domain in href:
                    links['internal'].append({'href': href, 'text': text})
                else:
                    links['external'].append({'href': href, 'text': text})
            elif href.startswith('/'):
                full_url = base_url + href
                links['internal'].append({'href': full_url, 'text': text})
            elif href.startswith('#'):
                # Skip anchor links
                continue
            elif not href.startswith(('mailto:', 'tel:', 'javascript:')):
                full_url = url.rstrip('/') + '/' + href.lstrip('/')
                links['internal'].append({'href': full_url, 'text': text})
        
        # Extract media with better handling
        media = {'images': [], 'videos': [], 'audio': []}
        
        # Images
        for img in soup.find_all('img', src=True):
            src = img['src']
            alt = img.get('alt', '')
            title_attr = img.get('title', '')
            
            if not src.startswith('http'):
                if src.startswith('/'):
                    src = base_url + src
                else:
                    src = url.rstrip('/') + '/' + src.lstrip('/')
            
            media['images'].append({
                'src': src, 
                'alt': alt, 
                'title': title_attr,
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
            
        # Videos
        for video in soup.find_all('video'):
            src = video.get('src', '')
            if not src:
                source = video.find('source')
                src = source.get('src', '') if source else ''
            
            if src and not src.startswith('http'):
                if src.startswith('/'):
                    src = base_url + src
                else:
                    src = url.rstrip('/') + '/' + src.lstrip('/')
            
            if src:
                media['videos'].append({
                    'src': src,
                    'type': video.get('type', ''),
                    'controls': video.has_attr('controls')
                })
        
        # Audio
        for audio in soup.find_all('audio'):
            src = audio.get('src', '')
            if not src:
                source = audio.find('source')
                src = source.get('src', '') if source else ''
            
            if src and not src.startswith('http'):
                if src.startswith('/'):
                    src = base_url + src
                else:
                    src = url.rstrip('/') + '/' + src.lstrip('/')
            
            if src:
                media['audio'].append({
                    'src': src,
                    'type': audio.get('type', ''),
                    'controls': audio.has_attr('controls')
                })
        
        # Extract structured data (JSON-LD)
        structured_data = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except:
                continue
        
        # Extract headings structure
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text().strip(),
                    'id': heading.get('id', '')
                })
        
        return {
            'success': True,
            'url': url,
            'title': title_text,
            'markdown': markdown_content,
            'cleaned_html': str(soup)[:10000],  # Increased limit
            'links': links,
            'media': media,
            'metadata': {
                'method': 'HTTP + BeautifulSoup',
                'description': description,
                'word_count': len(words),
                'structured_data': structured_data,
                'headings': headings,
                'timestamp': datetime.now().isoformat()
            },
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
    pdf: bool = False,
    extraction_strategy: str = "markdown",
    chunking_strategy: str = "regex",
    content_filter: str = "none",
    cache_mode: str = "enabled",
    delay_before_return: float = 2.0,
    page_timeout: int = 30000,
    remove_overlay_elements: bool = True
) -> Dict[str, Any]:
    """Full-featured browser-based crawling with all Crawl4AI capabilities"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Create comprehensive browser config
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
                "--max_old_space_size=1024",
                "--disable-background-mode",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-translate",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
            ]
        )
        
        # Use context manager for proper cleanup
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Configure crawler run with all options
            config = CrawlerRunConfig(
                word_count_threshold=word_count_threshold,
                screenshot=screenshot,
                pdf=pdf,
                page_timeout=page_timeout,
                delay_before_return_html=delay_before_return,
                remove_overlay_elements=remove_overlay_elements,
                cache_mode=CacheMode.ENABLED if cache_mode == "enabled" else CacheMode.DISABLED,
            )
            
            # Add CSS selector if provided
            if css_selector.strip():
                config.css_selector = css_selector.strip()
            
            # Configure extraction strategy
            if extraction_type == "llm" and custom_prompt.strip():
                config.extraction_strategy = LLMExtractionStrategy(
                    provider="openai/gpt-4o-mini",
                    api_token=os.getenv("OPENAI_API_KEY", ""),
                    instruction=custom_prompt
                )
            elif extraction_type == "json_css" and css_selector.strip():
                # JSON CSS extraction for structured data
                schema = {
                    "name": "Extracted Data",
                    "baseSelector": css_selector.strip(),
                    "fields": [
                        {"name": "text", "selector": "", "type": "text"},
                        {"name": "href", "selector": "a", "type": "attribute", "attribute": "href"},
                        {"name": "src", "selector": "img", "type": "attribute", "attribute": "src"}
                    ]
                }
                config.extraction_strategy = JsonCssExtractionStrategy(schema=schema)
            elif extraction_type == "regex" and custom_prompt.strip():
                # Use custom prompt as regex pattern
                config.extraction_strategy = RegexExtractionStrategy(patterns=[custom_prompt])
            
            # Configure chunking strategy
            if chunking_strategy == "nlp":
                config.chunking_strategy = NlpSentenceChunking()
            elif chunking_strategy == "fixed_length":
                config.chunking_strategy = FixedLengthWordChunking(chunk_size=500)
            elif chunking_strategy == "regex":
                config.chunking_strategy = RegexChunking()
            
            # Configure content filter
            if content_filter == "bm25":
                config.content_filter = BM25ContentFilter()
            elif content_filter == "pruning":
                config.content_filter = PruningContentFilter(threshold=0.5)
                
            # Perform crawl with timeout
            result = await asyncio.wait_for(
                crawler.arun(url=url, config=config),
                timeout=120  # 2 minute timeout
            )
            
            if not result or len(result) == 0:
                return {"error": "No results returned from crawler"}
                
            crawl_result = result[0]
            
            # Prepare comprehensive response
            response = {
                "success": crawl_result.success,
                "url": crawl_result.url,
                "title": getattr(crawl_result, 'title', 'N/A'),
                "markdown": crawl_result.markdown,
                "cleaned_html": crawl_result.cleaned_html[:10000] if crawl_result.cleaned_html else "",
                "links": crawl_result.links,
                "media": crawl_result.media,
                "metadata": crawl_result.metadata,
                "error_message": crawl_result.error_message
            }
            
            # Add extraction results if available
            if hasattr(crawl_result, 'extracted_content') and crawl_result.extracted_content:
                response["extracted_content"] = crawl_result.extracted_content
            
            # Add fit markdown if available
            if hasattr(crawl_result, 'fit_markdown') and crawl_result.fit_markdown:
                response["fit_markdown"] = crawl_result.fit_markdown
            
            # Add session ID if available
            if hasattr(crawl_result, 'session_id') and crawl_result.session_id:
                response["session_id"] = crawl_result.session_id
                
            # Handle screenshot
            if screenshot and crawl_result.screenshot:
                response["screenshot"] = crawl_result.screenshot
                
            # Handle PDF
            if pdf and crawl_result.pdf:
                response["pdf_size"] = len(crawl_result.pdf)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(crawl_result.pdf)
                    response["pdf_path"] = tmp.name
            
            # Add method info
            response["metadata"] = response.get("metadata", {})
            response["metadata"]["method"] = "Browser (Full Crawl4AI)"
            response["metadata"]["extraction_type"] = extraction_type
            response["metadata"]["chunking_strategy"] = chunking_strategy
            response["metadata"]["content_filter"] = content_filter
                    
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

def crawl_url(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf, 
              extraction_strategy, chunking_strategy, content_filter, cache_mode, 
              delay_before_return, page_timeout, remove_overlay_elements):
    """Main crawl function with comprehensive options and smart fallback"""
    try:
        # For advanced features, try browser first if available
        if BROWSER_AVAILABLE and CRAWL4AI_AVAILABLE and (screenshot or pdf or extraction_type in ["llm", "json_css", "regex"]):
            try:
                print("🚀 Using full browser crawling with advanced features...")
                result = asyncio.run(
                    browser_crawl(
                        url, extraction_type, custom_prompt, word_count, css_selector, 
                        screenshot, pdf, extraction_strategy, chunking_strategy, 
                        content_filter, cache_mode, delay_before_return, page_timeout, 
                        remove_overlay_elements
                    )
                )
                if "error" not in result:
                    return result
                else:
                    print(f"❌ Browser crawling failed: {result['error']}")
                    if not screenshot and not pdf:  # Can fallback for text-only
                        print("🔄 Falling back to HTTP crawling...")
                    else:
                        return result  # Can't fallback for visual features
            except Exception as e:
                print(f"❌ Browser crawling exception: {e}")
                if not screenshot and not pdf:
                    print("🔄 Falling back to HTTP crawling...")
                else:
                    return {
                        "error": f"Browser crawling failed and cannot fallback for visual features: {str(e)}",
                        "traceback": traceback.format_exc()
                    }
        
        # For simple requests or when browser isn't available, use HTTP
        if not screenshot and not pdf:
            print("🌐 Using HTTP crawling...")
            result = http_crawl(url, css_selector, word_count)
            return result
        else:
            return {
                "error": "Screenshots and PDF generation require browser automation, which is not available.",
                "traceback": "Browser features requested but browser automation is not working."
            }
            
    except Exception as e:
        return {
            "error": f"All crawling methods failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

def format_result(result: Dict[str, Any]) -> tuple:
    """Format the crawl result for comprehensive Gradio display"""
    if "error" in result:
        error_msg = result["error"]
        if "traceback" in result:
            error_msg += f"\n\nTechnical Details:\n{result['traceback']}"
        return error_msg, "", "", "", "", None, None, ""
    
    # Format basic info
    method = result.get('metadata', {}).get('method', 'Unknown')
    extraction_type = result.get('metadata', {}).get('extraction_type', 'N/A')
    word_count = result.get('metadata', {}).get('word_count', 'N/A')
    
    info = f"""
**URL:** {result.get('url', 'N/A')}
**Title:** {result.get('title', 'N/A')}
**Success:** {result.get('success', False)}
**Method:** {method}
**Extraction Type:** {extraction_type}
**Word Count:** {word_count}
**Error:** {result.get('error_message', 'None')}
"""
    
    # Get markdown content
    markdown = result.get('markdown', 'No content extracted')
    
    # Get extracted content if available
    extracted_content = ""
    if result.get('extracted_content'):
        if isinstance(result['extracted_content'], str):
            extracted_content = result['extracted_content']
        else:
            extracted_content = json.dumps(result['extracted_content'], indent=2)
    
    # Format links with better organization
    links_info = ""
    if result.get('links'):
        internal_links = result['links'].get('internal', [])
        external_links = result['links'].get('external', [])
        links_info = f"**Internal Links:** {len(internal_links)}\n**External Links:** {len(external_links)}\n\n"
        
        if internal_links:
            links_info += "**Internal Links:**\n"
            for i, link in enumerate(internal_links[:15]):  # Show more links
                links_info += f"{i+1}. [{link.get('text', 'No text')[:50]}...]({link.get('href', '#')})\n"
        
        if external_links:
            links_info += "\n**External Links:**\n"
            for i, link in enumerate(external_links[:15]):
                links_info += f"{i+1}. [{link.get('text', 'No text')[:50]}...]({link.get('href', '#')})\n"
    
    # Format comprehensive media info
    media_info = ""
    if result.get('media'):
        images = result['media'].get('images', [])
        videos = result['media'].get('videos', [])
        audio = result['media'].get('audio', [])
        
        media_info = f"**Images:** {len(images)}\n**Videos:** {len(videos)}\n**Audio:** {len(audio)}\n\n"
        
        if images:
            media_info += "**Images:**\n"
            for i, img in enumerate(images[:10]):
                alt_text = img.get('alt', 'No alt text')[:30]
                media_info += f"{i+1}. ![{alt_text}]({img.get('src', '#')}) - {img.get('title', 'No title')}\n"
        
        if videos:
            media_info += "\n**Videos:**\n"
            for i, video in enumerate(videos[:5]):
                media_info += f"{i+1}. [Video]({video.get('src', '#')}) - Type: {video.get('type', 'Unknown')}\n"
        
        if audio:
            media_info += "\n**Audio:**\n"
            for i, aud in enumerate(audio[:5]):
                media_info += f"{i+1}. [Audio]({aud.get('src', '#')}) - Type: {aud.get('type', 'Unknown')}\n"
    
    # Format metadata
    metadata_info = ""
    if result.get('metadata'):
        metadata = result['metadata']
        metadata_info = f"**Timestamp:** {metadata.get('timestamp', 'N/A')}\n"
        metadata_info += f"**Description:** {metadata.get('description', 'N/A')}\n"
        
        if metadata.get('headings'):
            metadata_info += f"\n**Page Structure:**\n"
            for heading in metadata['headings'][:10]:
                level = "  " * (heading['level'] - 1)
                metadata_info += f"{level}H{heading['level']}: {heading['text']}\n"
        
        if metadata.get('structured_data'):
            metadata_info += f"\n**Structured Data Found:** {len(metadata['structured_data'])} items\n"
    
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
    
    return info, markdown, extracted_content, links_info, media_info, screenshot_file, pdf_file, metadata_info

def crawl_interface(url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf,
                   extraction_strategy, chunking_strategy, content_filter, cache_mode, 
                   delay_before_return, page_timeout, remove_overlay_elements):
    """Comprehensive Gradio interface function"""
    if not url.strip():
        return "Please enter a URL to crawl.", "", "", "", "", None, None, ""
    
    try:
        result = crawl_url(
            url, extraction_type, custom_prompt, word_count, css_selector, screenshot, pdf,
            extraction_strategy, chunking_strategy, content_filter, cache_mode, 
            delay_before_return, page_timeout, remove_overlay_elements
        )
        return format_result(result)
    except Exception as e:
        error_msg = f"Interface error: {str(e)}\n\nTechnical Details:\n{traceback.format_exc()}"
        return error_msg, "", "", "", "", None, None, ""

# Create comprehensive Gradio interface
def create_interface():
    browser_status = "✅ Available" if BROWSER_AVAILABLE else "❌ Not Available (HTTP fallback active)"
    crawl4ai_status = "✅ Available" if CRAWL4AI_AVAILABLE else "❌ Not Available"
    
    with gr.Blocks(title="Crawl4AI - Full-Featured Web Crawler", theme=gr.themes.Soft()) as demo:
        gr.Markdown(f"""
        # 🚀🤖 Crawl4AI: Full-Featured Web Crawler & Scraper
        
        **Complete Crawl4AI functionality with robust HTTP fallback!**
        
        **System Status:**
        - **Crawl4AI Library:** {crawl4ai_status}
        - **Browser Automation:** {browser_status}
        - **HTTP Fallback:** ✅ Always Available
        
        **🔥 Full Features Available:**
        - 📄 **LLM-Ready Markdown** - Clean, structured output
        - 🖼️ **Screenshots & PDFs** {'✅ Available' if BROWSER_AVAILABLE else '❌ Requires browser'}
        - 🤖 **AI-Powered Extraction** - Custom prompts and LLM processing {'✅ Available' if BROWSER_AVAILABLE else '❌ Requires browser'}
        - 🎯 **Advanced Targeting** - CSS selectors, regex patterns, JSON extraction
        - 📊 **Multiple Strategies** - Chunking, filtering, and extraction options
        - 🔗 **Comprehensive Analysis** - Links, media, structured data
        - ⚡ **Smart Fallback** - Always works with HTTP backup
        - 🚀 **Performance Optimized** - Caching, timeouts, overlay removal
        """)
        
        with gr.Tabs():
            # Basic Tab
            with gr.TabItem("🚀 Basic Crawling"):
                with gr.Row():
                    with gr.Column(scale=2):
                        url_input = gr.Textbox(
                            label="🌐 URL to Crawl",
                            placeholder="https://example.com",
                            value="https://docs.crawl4ai.com/first-steps/introduction"
                        )
                        
                        with gr.Row():
                            extraction_type = gr.Radio(
                                choices=["markdown", "llm", "json_css", "regex"],
                                value="markdown",
                                label="📊 Extraction Type",
                                info="Markdown: Clean text | LLM: AI-powered | JSON CSS: Structured | Regex: Pattern-based"
                            )
                            
                        with gr.Row():
                            screenshot_check = gr.Checkbox(
                                label="📸 Take Screenshot", 
                                value=False,
                                interactive=BROWSER_AVAILABLE,
                                info="Requires browser automation"
                            )
                            pdf_check = gr.Checkbox(
                                label="📄 Generate PDF", 
                                value=False,
                                interactive=BROWSER_AVAILABLE,
                                info="Requires browser automation"
                            )
                        
                        custom_prompt = gr.Textbox(
                            label="🤖 Custom Prompt/Pattern",
                            placeholder="For LLM: 'Extract all product names and prices' | For Regex: '\\d+\\.\\d+' | For JSON CSS: Use CSS selector below",
                            lines=3,
                            info="Used for LLM instructions, regex patterns, or JSON CSS extraction"
                        )
                        
                        css_selector = gr.Textbox(
                            label="🎯 CSS Selector (optional)",
                            placeholder="article, .content, #main, .product-item",
                            info="Target specific elements on the page"
                        )
                        
                        word_count = gr.Slider(
                            minimum=1,
                            maximum=200,
                            value=10,
                            step=1,
                            label="📝 Word Count Threshold",
                            info="Minimum words required for content blocks"
                        )
                        
                        crawl_btn = gr.Button("🚀 Crawl Website", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        gr.Markdown(f"""
                        ### 💡 Extraction Types:
                        
                        **📄 Markdown** (Always works)
                        - Clean, readable text extraction
                        - Perfect for content analysis
                        - Works with HTTP fallback
                        
                        **🤖 LLM** {'✅ Available' if BROWSER_AVAILABLE else '❌ Browser required'}
                        - AI-powered custom extraction
                        - Use natural language prompts
                        - Requires OpenAI API key in environment
                        
                        **📊 JSON CSS** {'✅ Available' if BROWSER_AVAILABLE else '❌ Browser required'}
                        - Structured data extraction
                        - Uses CSS selectors for targeting
                        - Returns organized JSON data
                        
                        **🔍 Regex** {'✅ Available' if BROWSER_AVAILABLE else '❌ Browser required'}
                        - Pattern-based extraction
                        - Use regex patterns in prompt field
                        - Great for specific data formats
                        
                        ### 🎯 CSS Selector Examples:
                        - `article` - Main article content
                        - `.product-item` - Product listings
                        - `#main-content` - Main content area
                        - `h1, h2, h3` - All headings
                        - `.price, .cost` - Price elements
                        """)
            
            # Advanced Tab
            with gr.TabItem("⚙️ Advanced Options"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🔧 Processing Strategies")
                        
                        extraction_strategy = gr.Radio(
                            choices=["markdown", "llm", "json_css", "regex"],
                            value="markdown",
                            label="📊 Extraction Strategy",
                            info="How to extract content from the page"
                        )
                        
                        chunking_strategy = gr.Radio(
                            choices=["regex", "nlp", "fixed_length"],
                            value="regex",
                            label="✂️ Chunking Strategy",
                            info="How to split content into chunks"
                        )
                        
                        content_filter = gr.Radio(
                            choices=["none", "bm25", "pruning"],
                            value="none",
                            label="🔍 Content Filter",
                            info="Filter content quality and relevance"
                        )
                    
                    with gr.Column():
                        gr.Markdown("### ⚡ Performance Settings")
                        
                        cache_mode = gr.Radio(
                            choices=["enabled", "disabled"],
                            value="enabled",
                            label="💾 Cache Mode",
                            info="Enable caching for faster repeated requests"
                        )
                        
                        delay_before_return = gr.Slider(
                            minimum=0.0,
                            maximum=10.0,
                            value=2.0,
                            step=0.5,
                            label="⏱️ Delay Before Return (seconds)",
                            info="Wait time for page to fully load"
                        )
                        
                        page_timeout = gr.Slider(
                            minimum=10000,
                            maximum=120000,
                            value=30000,
                            step=5000,
                            label="⏰ Page Timeout (milliseconds)",
                            info="Maximum time to wait for page load"
                        )
                        
                        remove_overlay_elements = gr.Checkbox(
                            label="🚫 Remove Overlay Elements",
                            value=True,
                            info="Remove popups, modals, and overlay elements"
                        )
                
                gr.Markdown("""
                ### 📚 Strategy Explanations:
                
                **Chunking Strategies:**
                - **Regex**: Split by patterns (paragraphs, sentences)
                - **NLP**: Natural language processing for sentence boundaries
                - **Fixed Length**: Split into fixed word count chunks
                
                **Content Filters:**
                - **None**: No filtering, return all content
                - **BM25**: Relevance-based filtering using BM25 algorithm
                - **Pruning**: Remove low-quality content based on thresholds
                
                **Performance Tips:**
                - Enable caching for repeated requests to same URLs
                - Increase delay for JavaScript-heavy sites
                - Adjust timeout based on site complexity
                - Remove overlays to avoid popup interference
                """)
        
        # Output sections with comprehensive display
        gr.Markdown("## 📊 Results")
        
        with gr.Row():
            with gr.Column():
                info_output = gr.Markdown(label="ℹ️ Page Information")
        
        with gr.Tabs():
            with gr.TabItem("📝 Markdown Content"):
                markdown_output = gr.Textbox(
                    label="Extracted Markdown",
                    lines=25,
                    max_lines=40,
                    show_copy_button=True,
                    info="Clean, LLM-ready markdown content"
                )
            
            with gr.TabItem("🎯 Extracted Content"):
                extracted_output = gr.Textbox(
                    label="Custom Extracted Content",
                    lines=20,
                    max_lines=30,
                    show_copy_button=True,
                    info="Results from LLM, JSON CSS, or Regex extraction"
                )
            
            with gr.TabItem("🔗 Links Analysis"):
                links_output = gr.Markdown(
                    label="Links Found",
                    info="Internal and external links with text and URLs"
                )
                
            with gr.TabItem("🖼️ Media Analysis"):
                media_output = gr.Markdown(
                    label="Media Elements",
                    info="Images, videos, and audio files found on the page"
                )
            
            with gr.TabItem("📸 Screenshot"):
                screenshot_output = gr.Image(
                    label="Page Screenshot", 
                    type="filepath",
                    info="Full-page screenshot (requires browser automation)"
                )
                
            with gr.TabItem("📄 PDF"):
                pdf_output = gr.File(
                    label="Generated PDF",
                    info="PDF version of the page (requires browser automation)"
                )
            
            with gr.TabItem("📊 Metadata"):
                metadata_output = gr.Markdown(
                    label="Page Metadata",
                    info="Structured data, headings, timestamps, and technical details"
                )
        
        # Connect the interface with all parameters
        crawl_btn.click(
            fn=crawl_interface,
            inputs=[
                url_input, extraction_type, custom_prompt, word_count, css_selector, 
                screenshot_check, pdf_check, extraction_strategy, chunking_strategy, 
                content_filter, cache_mode, delay_before_return, page_timeout, 
                remove_overlay_elements
            ],
            outputs=[
                info_output, markdown_output, extracted_output, links_output, 
                media_output, screenshot_output, pdf_output, metadata_output
            ]
        )
        
        # Comprehensive examples
        gr.Examples(
            examples=[
                # Basic examples
                ["https://docs.crawl4ai.com/first-steps/introduction", "markdown", "", 10, "", False, False, "markdown", "regex", "none", "enabled", 2.0, 30000, True],
                ["https://example.com", "markdown", "", 10, "", False, False, "markdown", "regex", "none", "enabled", 2.0, 30000, True],
                # Advanced examples
                ["https://news.ycombinator.com", "json_css", "", 5, ".storylink", False, False, "json_css", "regex", "none", "enabled", 3.0, 45000, True],
                ["https://docs.crawl4ai.com", "llm", "Extract all the main features and benefits mentioned", 10, "", False, False, "llm", "nlp", "bm25", "enabled", 2.0, 30000, True],
            ],
            inputs=[
                url_input, extraction_type, custom_prompt, word_count, css_selector, 
                screenshot_check, pdf_check, extraction_strategy, chunking_strategy, 
                content_filter, cache_mode, delay_before_return, page_timeout, 
                remove_overlay_elements
            ]
        )
        
        gr.Markdown(f"""
        ---
        ## 🎯 Full-Featured Crawl4AI Experience
        
        **Current Capabilities:**
        - **Browser Automation:** {browser_status}
        - **Full Crawl4AI:** {crawl4ai_status}
        - **HTTP Fallback:** ✅ Always Available
        
        **🚀 What's Included:**
        - All extraction strategies (Markdown, LLM, JSON CSS, Regex)
        - Multiple chunking options (Regex, NLP, Fixed Length)
        - Content filtering (BM25, Pruning)
        - Performance optimization (Caching, Timeouts)
        - Visual capture (Screenshots, PDFs)
        - Comprehensive analysis (Links, Media, Metadata)
        - Smart fallback system for reliability
        
        **🔗 Learn More:**
        - [Crawl4AI Documentation](https://docs.crawl4ai.com)
        - [GitHub Repository](https://github.com/unclecode/crawl4ai)
        - [API Documentation](https://docs.crawl4ai.com/api)
        
        **Built with ❤️ by the Crawl4AI community**
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