"""
Crawl4AI FastAPI Server for Hugging Face Spaces
- Exposes API endpoints for web crawling
- Includes MCP server endpoints
- Configured for Hugging Face Spaces deployment
"""

import os
import sys
import time
import asyncio
import pathlib
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import yaml
from fastapi import FastAPI, HTTPException, Request, Path, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from redis import asyncio as aioredis
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator

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

# Global page semaphore (hard cap)
MAX_PAGES = config["crawler"]["pool"].get("max_pages", 20)
GLOBAL_SEM = asyncio.Semaphore(MAX_PAGES)

# Patch AsyncWebCrawler.arun to use the semaphore
orig_arun = AsyncWebCrawler.arun

async def capped_arun(self, *a, **kw):
    async with GLOBAL_SEM:
        return await orig_arun(self, *a, **kw)

AsyncWebCrawler.arun = capped_arun

# Create a crawler pool
crawler_instances = {}

async def get_crawler(browser_config=None):
    """Get or create a crawler instance"""
    if browser_config is None:
        browser_config = BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {})
        )
    
    key = str(browser_config.model_dump())
    if key not in crawler_instances:
        crawler_instances[key] = await AsyncWebCrawler.create(config=browser_config)
    
    return crawler_instances[key]

async def close_all():
    """Close all crawler instances"""
    for crawler in crawler_instances.values():
        await crawler.aclose()
    crawler_instances.clear()

async def janitor():
    """Periodically check for idle crawlers and close them"""
    idle_ttl = config["crawler"]["pool"].get("idle_ttl_sec", 1800)
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        # Implementation would check last usage time and close idle crawlers

# FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up a crawler instance
    await get_crawler(BrowserConfig(
        extra_args=config["crawler"]["browser"].get("extra_args", []),
        **config["crawler"]["browser"].get("kwargs", {})
    ))
    # Start the janitor task
    app.state.janitor = asyncio.create_task(janitor())
    yield
    # Clean up
    app.state.janitor.cancel()
    await close_all()

# Create FastAPI app
app = FastAPI(
    title=config["app"]["title"],
    version=config["app"]["version"],
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Redis
redis = aioredis.from_url(f"redis://{config['redis']['host']}:{config['redis']['port']}")

# Set up rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[config["rate_limiting"]["default_limit"]],
    storage_uri=config["rate_limiting"]["storage_uri"],
)

# Set up Prometheus metrics
if config["observability"]["prometheus"]["enabled"]:
    Instrumentator().instrument(app).expose(app)

# Pydantic models for API requests
class CrawlRequest(BaseModel):
    urls: List[str]
    browser_config: Optional[dict] = None
    crawler_config: Optional[dict] = None

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
    output_path: Optional[str] = None

class PDFRequest(BaseModel):
    url: str
    output_path: Optional[str] = None

class JSEndpointRequest(BaseModel):
    url: str
    scripts: List[str]

class RawCode(BaseModel):
    code: str

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
@limiter.limit(config["rate_limiting"]["default_limit"])
async def get_markdown(request: Request, body: MarkdownRequest):
    """
    Convert a webpage to markdown format
    """
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(400, "URL must be absolute and start with http/https")
    
    try:
        async with AsyncWebCrawler(config=BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {})
        )) as crawler:
            results = await crawler.arun(url=body.url, config=CrawlerRunConfig())
            
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to crawl the URL")
            
        markdown = results[0].markdown
        
        return JSONResponse({
            "url": body.url,
            "filter": body.f,
            "query": body.q,
            "cache": body.c,
            "markdown": markdown,
            "success": True
        })
    except Exception as e:
        logger.error(f"Error in /md endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/html")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def generate_html(request: Request, body: HTMLRequest):
    """
    Crawls the URL and returns the processed HTML
    """
    try:
        cfg = CrawlerRunConfig()
        async with AsyncWebCrawler(config=BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {})
        )) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to crawl the URL")
            
        raw_html = results[0].html
        from crawl4ai.utils import preprocess_html_for_schema
        processed_html = preprocess_html_for_schema(raw_html)
        
        return JSONResponse({
            "html": processed_html, 
            "url": body.url, 
            "success": True
        })
    except Exception as e:
        logger.error(f"Error in /html endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/screenshot")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def generate_screenshot(request: Request, body: ScreenshotRequest):
    """
    Capture a screenshot of the specified URL
    """
    try:
        cfg = CrawlerRunConfig(screenshot=True, screenshot_wait_for=body.screenshot_wait_for)
        async with AsyncWebCrawler(config=BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {})
        )) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to capture screenshot")
            
        screenshot_data = results[0].screenshot
        
        if body.output_path:
            import os
            import base64
            abs_path = os.path.abspath(body.output_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(base64.b64decode(screenshot_data))
            return {"success": True, "path": abs_path}
        
        return {"success": True, "screenshot": screenshot_data}
    except Exception as e:
        logger.error(f"Error in /screenshot endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/pdf")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def generate_pdf(request: Request, body: PDFRequest):
    """
    Generate a PDF of the specified URL
    """
    try:
        cfg = CrawlerRunConfig(pdf=True)
        async with AsyncWebCrawler(config=BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {})
        )) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to generate PDF")
            
        pdf_data = results[0].pdf
        
        if body.output_path:
            import os
            abs_path = os.path.abspath(body.output_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(pdf_data)
            return {"success": True, "path": abs_path}
        
        import base64
        return {"success": True, "pdf": base64.b64encode(pdf_data).decode()}
    except Exception as e:
        logger.error(f"Error in /pdf endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/execute_js")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def execute_js(request: Request, body: JSEndpointRequest):
    """
    Execute JavaScript on the specified URL
    """
    try:
        cfg = CrawlerRunConfig(js_code=body.scripts)
        async with AsyncWebCrawler(config=BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {})
        )) as crawler:
            results = await crawler.arun(url=body.url, config=cfg)
        
        if not results or not results[0].success:
            raise HTTPException(500, "Failed to execute JavaScript")
            
        data = results[0].model_dump()
        return JSONResponse(data)
    except Exception as e:
        logger.error(f"Error in /execute_js endpoint: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/crawl")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl(request: Request, crawl_request: CrawlRequest):
    """
    Crawl a list of URLs and return the results
    """
    if not crawl_request.urls:
        raise HTTPException(400, "At least one URL required")
    
    try:
        browser_config = BrowserConfig(
            extra_args=config["crawler"]["browser"].get("extra_args", []),
            **config["crawler"]["browser"].get("kwargs", {})
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
        
        return JSONResponse(results)
    except Exception as e:
        logger.error(f"Error in /crawl endpoint: {str(e)}")
        raise HTTPException(500, str(e))

# Import MCP bridge functionality
from mcp.server.lowlevel.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as t
from mcp.server.sse import SseServerTransport
import inspect
import json
import re
import anyio
import httpx

# MCP decorators
def mcp_resource(name: str = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "resource", name
        return fn
    return deco

def mcp_template(name: str = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "template", name
        return fn
    return deco

def mcp_tool(name: str = None):
    def deco(fn):
        fn.__mcp_kind__, fn.__mcp_name__ = "tool", name
        return fn
    return deco

# Apply MCP decorators to endpoints
get_markdown = mcp_tool("md")(get_markdown)
generate_html = mcp_tool("html")(generate_html)
generate_screenshot = mcp_tool("screenshot")(generate_screenshot)
generate_pdf = mcp_tool("pdf")(generate_pdf)
execute_js = mcp_tool("execute_js")(execute_js)
crawl = mcp_tool("crawl")(crawl)

# HTTP proxy helper for FastAPI endpoints
def _make_http_proxy(base_url: str, route):
    method = list(route.methods - {"HEAD", "OPTIONS"})[0]
    async def proxy(**kwargs):
        # Replace path parameters
        path = route.path
        for k, v in list(kwargs.items()):
            placeholder = "{" + k + "}"
            if placeholder in path:
                path = path.replace(placeholder, str(v))
                kwargs.pop(k)
        url = base_url.rstrip("/") + path

        async with httpx.AsyncClient() as client:
            try:
                r = (
                    await client.get(url, params=kwargs)
                    if method == "GET"
                    else await client.request(method, url, json=kwargs)
                )
                r.raise_for_status()
                return r.text if method == "GET" else r.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(e.response.status_code, e.response.text)
    return proxy

# Attach MCP server
def attach_mcp(
    app: FastAPI,
    *,
    base: str = "/mcp",
    name: str = None,
    base_url: str,
):
    """Attach MCP server to FastAPI app"""
    server_name = name or app.title or "FastAPI-MCP"
    mcp = Server(server_name)

    tools = {}
    resources = {}
    templates = {}

    # Register decorated FastAPI routes
    for route in app.routes:
        fn = getattr(route, "endpoint", None)
        kind = getattr(fn, "__mcp_kind__", None)
        if not kind:
            continue

        key = fn.__mcp_name__ or re.sub(r"[/{}}]", "_", route.path).strip("_")

        if kind == "tool":
            proxy = _make_http_proxy(base_url, route)
            tools[key] = (proxy, fn)
            continue
        if kind == "resource":
            resources[key] = fn
        if kind == "template":
            templates[key] = fn

    # Helpers for JSON Schema
    def _schema(model: type[BaseModel] = None) -> dict:
        return {"type": "object"} if model is None else model.model_json_schema()

    def _body_model(fn: callable) -> type[BaseModel]:
        for p in inspect.signature(fn).parameters.values():
            a = p.annotation
            if inspect.isclass(a) and issubclass(a, BaseModel):
                return a
        return None

    # MCP handlers
    @mcp.list_tools()
    async def _list_tools() -> List[t.Tool]:
        out = []
        for k, (proxy, orig_fn) in tools.items():
            desc = getattr(orig_fn, "__mcp_description__", None) or inspect.getdoc(orig_fn) or ""
            schema = getattr(orig_fn, "__mcp_schema__", None) or _schema(_body_model(orig_fn))
            out.append(
                t.Tool(name=k, description=desc, inputSchema=schema)
            )
        return out

    @mcp.call_tool()
    async def _call_tool(name: str, arguments: Dict = None) -> List[t.TextContent]:
        if name not in tools:
            raise HTTPException(404, "tool not found")
        
        proxy, _ = tools[name]
        try:
            res = await proxy(**(arguments or {}))
        except HTTPException as exc:
            # Map server-side errors into MCP "text/error" payloads
            err = {"error": exc.status_code, "detail": exc.detail}
            return [t.TextContent(type="text", text=json.dumps(err))]
        return [t.TextContent(type="text", text=json.dumps(res, default=str))]

    @mcp.list_resources()
    async def _list_resources() -> List[t.Resource]:
        return [
            t.Resource(name=k, description=inspect.getdoc(f) or "", mime_type="application/json")
            for k, f in resources.items()
        ]

    @mcp.read_resource()
    async def _read_resource(name: str) -> List[t.TextContent]:
        if name not in resources:
            raise HTTPException(404, "resource not found")
        res = resources[name]()
        return [t.TextContent(type="text", text=json.dumps(res, default=str))]

    @mcp.list_resource_templates()
    async def _list_templates() -> List[t.ResourceTemplate]:
        return [
            t.ResourceTemplate(
                name=k,
                description=inspect.getdoc(f) or "",
                parameters={
                    p: {"type": "string"} for p in _path_params(app, f)
                },
            )
            for k, f in templates.items()
        ]

    def _path_params(app: FastAPI, fn: callable) -> List[str]:
        for r in app.routes:
            if r.endpoint is fn:
                return list(r.param_convertors.keys())
        return []

    init_opts = InitializationOptions(
        server_name=server_name,
        server_version="0.1.0",
        capabilities=mcp.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    )

    # WebSocket transport
    @app.websocket_route(f"{base}/ws")
    async def _ws(ws: WebSocket):
        await ws.accept()
        c2s_send, c2s_recv = anyio.create_memory_object_stream(100)
        s2c_send, s2c_recv = anyio.create_memory_object_stream(100)

        from pydantic import TypeAdapter
        from mcp.types import JSONRPCMessage
        adapter = TypeAdapter(JSONRPCMessage)

        init_done = anyio.Event()

        async def srv_to_ws():
            first = True 
            try:
                async for msg in s2c_recv:
                    await ws.send_json(msg.model_dump())
                    if first:
                        init_done.set()
                        first = False
            finally:
                # Make sure cleanup survives TaskGroup cancellation
                with anyio.CancelScope(shield=True):
                    with asyncio.suppress(RuntimeError):  # Idempotent close
                        await ws.close()

        async def ws_to_srv():
            try:
                # 1st frame is always "initialize"
                first = adapter.validate_python(await ws.receive_json())
                await c2s_send.send(first)
                await init_done.wait()  # Block until server ready
                while True:
                    data = await ws.receive_json()
                    await c2s_send.send(adapter.validate_python(data))
            except WebSocketDisconnect:
                await c2s_send.aclose()

        async with anyio.create_task_group() as tg:
            tg.start_soon(mcp.run, c2s_recv, s2c_send, init_opts)
            tg.start_soon(ws_to_srv)
            tg.start_soon(srv_to_ws)

    # SSE transport
    sse = SseServerTransport(f"{base}/messages/")

    @app.get(f"{base}/sse")
    async def _mcp_sse(request: Request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send  # Starlette ASGI primitives
        ) as (read_stream, write_stream):
            await mcp.run(read_stream, write_stream, init_opts)

    # Client → server frames are POSTed here
    app.mount(f"{base}/messages", app=sse.handle_post_message)

    # Schema endpoint
    @app.get(f"{base}/schema")
    async def _schema_endpoint():
        return JSONResponse({
            "tools": [x.model_dump() for x in await _list_tools()],
            "resources": [x.model_dump() for x in await _list_resources()],
            "resource_templates": [x.model_dump() for x in await _list_templates()],
        })

# Attach MCP server
base_url = f"http://localhost:{config['app']['port']}"
attach_mcp(app, base="/mcp", name="Crawl4AI-MCP", base_url=base_url)

# Run the app if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config["app"]["host"],
        port=config["app"]["port"],
        reload=config["app"]["reload"]
    )