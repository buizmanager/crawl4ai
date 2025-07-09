"""
Crawl4AI API for Hugging Face Spaces
- Provides a Gradio UI for testing the API
- Exposes FastAPI endpoints for web crawling
- Includes MCP server endpoints
"""

import os
import sys
import time
import asyncio
import json
import base64
from typing import Dict, List, Optional

import gradio as gr
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import Crawl4AI
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
except ImportError:
    # Install Crawl4AI if not available
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "crawl4ai>=0.6.0"])
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

config = load_config()

# Set up logging
import logging
logging.basicConfig(
    level=getattr(logging, config["logging"]["level"]),
    format=config["logging"]["format"]
)
logger = logging.getLogger("crawl4ai")

# Pydantic models for API requests
class MarkdownRequest(BaseModel):
    url: str
    f: Optional[str] = None  # filter
    q: Optional[str] = None  # query
    c: Optional[bool] = True  # cache

class HTMLRequest(BaseModel):
    url: str

class ScreenshotRequest(BaseModel):
    url: str
    screenshot_wait_for: Optional[str] = None

class PDFRequest(BaseModel):
    url: str

class JSEndpointRequest(BaseModel):
    url: str
    scripts: List[str]

class CrawlRequest(BaseModel):
    urls: List[str]
    browser_config: Optional[dict] = None
    crawler_config: Optional[dict] = None

# Create FastAPI app
app = FastAPI(
    title=config["app"]["title"],
    version=config["app"]["version"],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints
@app.get("/")
async def root():
    return {
        "message": "Welcome to Crawl4AI API",
        "version": config["app"]["version"],
        "docs_url": "/docs",
        "health_check": config["observability"]["health_check"]["endpoint"]
    }

@app.get(config["observability"]["health_check"]["endpoint"])
async def health():
    return {"status": "ok", "timestamp": time.time()}

@app.post("/md")
async def get_markdown(body: MarkdownRequest):
    """
    Convert a webpage to markdown format
    """
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(400, "URL must be absolute and start with http/https")
    
    try:
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=body.url, config=CrawlerRunConfig())
            
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to crawl the URL")
            
        markdown = results[0].markdown
        
        return {
            "url": body.url,
            "filter": body.f,
            "query": body.q,
            "cache": body.c,
            "markdown": markdown,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in /md endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/html")
async def generate_html(body: HTMLRequest):
    """
    Crawls the URL and returns the processed HTML
    """
    try:
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=body.url, config=CrawlerRunConfig())
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to crawl the URL")
            
        raw_html = results[0].html
        from crawl4ai.utils import preprocess_html_for_schema
        processed_html = preprocess_html_for_schema(raw_html)
        
        return {
            "html": processed_html, 
            "url": body.url, 
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in /html endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/screenshot")
async def generate_screenshot(body: ScreenshotRequest):
    """
    Capture a screenshot of the specified URL
    """
    try:
        cfg = CrawlerRunConfig(screenshot=True, screenshot_wait_for=body.screenshot_wait_for)
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to capture screenshot")
            
        screenshot_data = results[0].screenshot
        return {"success": True, "screenshot": screenshot_data}
    except Exception as e:
        logger.error(f"Error in /screenshot endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/pdf")
async def generate_pdf(body: PDFRequest):
    """
    Generate a PDF of the specified URL
    """
    try:
        cfg = CrawlerRunConfig(pdf=True)
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to generate PDF")
            
        pdf_data = results[0].pdf
        return {"success": True, "pdf": base64.b64encode(pdf_data).decode()}
    except Exception as e:
        logger.error(f"Error in /pdf endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/execute_js")
async def execute_js(body: JSEndpointRequest):
    """
    Execute JavaScript on the specified URL
    """
    try:
        cfg = CrawlerRunConfig(js_code=body.scripts)
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to execute JavaScript")
            
        data = results[0].model_dump()
        return data
    except Exception as e:
        logger.error(f"Error in /execute_js endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/crawl")
async def crawl(crawl_request: CrawlRequest):
    """
    Crawl a list of URLs and return the results
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    
    try:
        browser_config = BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )
        if crawl_request.browser_config:
            browser_config = BrowserConfig.parse_obj(crawl_request.browser_config)
        
        crawler_config = CrawlerRunConfig()
        if crawl_request.crawler_config:
            crawler_config = CrawlerRunConfig.parse_obj(crawl_request.crawler_config)
        
        results = []
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for url in crawl_request.urls:
                try:
                    result = await crawler.arun(url=url, config=crawler_config)
                    results.extend([r.model_dump() for r in result])
                except Exception as e:
                    results.append({
                        "url": url,
                        "success": False,
                        "error_message": str(e)
                    })
        
        return results
    except Exception as e:
        logger.error(f"Error in /crawl endpoint: {str(e)}")
        raise HTTPException(500, str(e))

# Gradio UI functions
async def fetch_markdown(url):
    if not url:
        return "Please enter a URL"
    
    try:
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=url, config=CrawlerRunConfig())
            
        if not results or not results[0].success:
            return "Failed to crawl the URL"
            
        return results[0].markdown
    except Exception as e:
        logger.error(f"Error fetching markdown: {str(e)}")
        return f"Error: {str(e)}"

async def take_screenshot(url):
    if not url:
        return "Please enter a URL", None
    
    try:
        cfg = CrawlerRunConfig(screenshot=True)
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=url, config=cfg)
        
        if not results or not results[0].success:
            return "Failed to capture screenshot", None
            
        screenshot_data = results[0].screenshot
        import io
        from PIL import Image
        image_data = base64.b64decode(screenshot_data)
        image = Image.open(io.BytesIO(image_data))
        return "Screenshot captured successfully", image
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}")
        return f"Error: {str(e)}", None

async def execute_javascript(url, js_code):
    if not url:
        return "Please enter a URL"
    
    if not js_code:
        return "Please enter JavaScript code"
    
    try:
        scripts = [js_code]
        cfg = CrawlerRunConfig(js_code=scripts)
        async with AsyncWebCrawler(config=BrowserConfig(
            headless=True,
            extra_args=config["crawler"]["browser"].get("extra_args", [])
        )) as crawler:
            results = await crawler.arun(url=url, config=cfg)
        
        if not results or not results[0].success:
            return "Failed to execute JavaScript"
            
        js_result = results[0].js_execution_result
        return json.dumps(js_result, indent=2)
    except Exception as e:
        logger.error(f"Error executing JavaScript: {str(e)}")
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="Crawl4AI API") as demo:
    gr.Markdown("# Crawl4AI API")
    gr.Markdown("This is a demo of the Crawl4AI API. You can use the UI below to test the API or use the REST endpoints directly.")
    
    with gr.Tab("Markdown"):
        with gr.Row():
            with gr.Column():
                md_url = gr.Textbox(label="URL", placeholder="https://example.com")
                md_button = gr.Button("Convert to Markdown")
            with gr.Column():
                md_output = gr.Markdown(label="Markdown Output")
        md_button.click(fetch_markdown, inputs=[md_url], outputs=[md_output])
    
    with gr.Tab("Screenshot"):
        with gr.Row():
            with gr.Column():
                ss_url = gr.Textbox(label="URL", placeholder="https://example.com")
                ss_button = gr.Button("Take Screenshot")
            with gr.Column():
                ss_status = gr.Textbox(label="Status")
                ss_output = gr.Image(label="Screenshot")
        ss_button.click(take_screenshot, inputs=[ss_url], outputs=[ss_status, ss_output])
    
    with gr.Tab("JavaScript"):
        with gr.Row():
            with gr.Column():
                js_url = gr.Textbox(label="URL", placeholder="https://example.com")
                js_code = gr.Textbox(label="JavaScript Code", placeholder="document.title", lines=5)
                js_button = gr.Button("Execute JavaScript")
            with gr.Column():
                js_output = gr.Code(language="json", label="JavaScript Output")
        js_button.click(execute_javascript, inputs=[js_url, js_code], outputs=[js_output])
    
    with gr.Tab("API Documentation"):
        gr.Markdown("""
        ## API Endpoints
        
        The following REST API endpoints are available:
        
        - `GET /health` - Check if the API is running
        - `POST /md` - Convert a webpage to markdown
        - `POST /html` - Get processed HTML from a webpage
        - `POST /screenshot` - Take a screenshot of a webpage
        - `POST /pdf` - Generate a PDF of a webpage
        - `POST /execute_js` - Execute JavaScript on a webpage
        - `POST /crawl` - Crawl multiple URLs
        
        For full API documentation, visit the [Swagger UI](/docs) or [ReDoc](/redoc).
        """)

# Mount the Gradio app
app = gr.mount_gradio_app(app, demo, path="/")

# Run the app if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config["app"]["host"],
        port=config["app"]["port"],
        reload=config["app"]["reload"]
    )