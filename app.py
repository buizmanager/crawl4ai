#!/usr/bin/env python3
"""
Crawl4AI Remote API Client for Hugging Face Spaces
This app connects to a remote crawl4AI instance and provides a user interface to access its API endpoints.
"""

import gradio as gr
import json
import os
import sys
import traceback
from typing import Dict, Any, List, Optional
import asyncio
import base64
import tempfile
from datetime import datetime
import httpx
from dotenv import load_dotenv
import time
import uuid
import websockets
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Custom WebSocket client implementation
class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: Dict[str, Any]

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    result: Dict[str, Any]

# Configuration
CRAWL4AI_API_URL = os.getenv("CRAWL4AI_API_URL", "ws://localhost:11235/mcp/ws")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "ws://localhost:11235/mcp/ws")

class Crawl4AIClient:
    """Client for interacting with a remote Crawl4AI instance"""
    
    def __init__(self, api_url: str = CRAWL4AI_API_URL):
        self.api_url = api_url
        self.websocket = None
        self.initialized = False
        
    async def connect(self):
        """Connect to the MCP WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.api_url)
            
            # Initialize the connection
            init_id = str(uuid.uuid4())
            init_request = JsonRpcRequest(
                id=init_id,
                method="initialize",
                params={
                    "client_info": {
                        "name": "Crawl4AI Remote Client",
                        "version": "1.0.0"
                    }
                }
            )
            
            await self.websocket.send(init_request.model_dump_json())
            response = await self.websocket.recv()
            
            # Mark as initialized
            self.initialized = True
            return True
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False
            
    async def disconnect(self):
        """Disconnect from the MCP WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.initialized = False
        
    async def _send_request(self, method: str, params: Dict[str, Any]):
        """Send a request to the MCP server and get the response"""
        if not self.websocket or not self.initialized:
            if not await self.connect():
                return {"error": "Failed to connect to Crawl4AI server"}
        
        try:
            request_id = str(uuid.uuid4())
            request = JsonRpcRequest(
                id=request_id,
                method=method,
                params=params
            )
            
            await self.websocket.send(request.model_dump_json())
            response_text = await self.websocket.recv()
            response = json.loads(response_text)
            
            return response
        except Exception as e:
            return {"error": f"Request error: {str(e)}"}
        
    async def list_tools(self):
        """List available tools from the MCP server"""
        response = await self._send_request("workspace/listTools", {})
        
        if "error" in response:
            return response
        
        return {"tools": response.get("result", {}).get("tools", [])}
            
    async def crawl_url(self, url: str, css_selector: str = "", word_count_threshold: int = 5):
        """Crawl a URL using the remote Crawl4AI instance"""
        response = await self._send_request("workspace/callTool", {
            "name": "md",
            "arguments": {
                "url": url,
                "f": "fit",  # Format: fit, raw, bm25, llm
                "q": css_selector if css_selector else None,
                "c": str(word_count_threshold),
            }
        })
        
        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "url": url
            }
        
        try:
            # Parse the content from the response
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                result = json.loads(content[0].get("text", "{}"))
                return result
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "url": url
                }
        except Exception as e:
            traceback_str = traceback.format_exc()
            return {
                "success": False,
                "error": f"Error parsing response: {str(e)}",
                "traceback": traceback_str,
                "url": url
            }
    
    async def get_screenshot(self, url: str, wait_time: float = 1.0):
        """Get a screenshot of a URL using the remote Crawl4AI instance"""
        response = await self._send_request("workspace/callTool", {
            "name": "screenshot",
            "arguments": {
                "url": url,
                "screenshot_wait_for": wait_time,
            }
        })
        
        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "url": url
            }
        
        try:
            # Parse the content from the response
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                result = json.loads(content[0].get("text", "{}"))
                return result
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "url": url
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting screenshot: {str(e)}",
                "traceback": traceback.format_exc(),
                "url": url
            }
    
    async def get_pdf(self, url: str):
        """Get a PDF of a URL using the remote Crawl4AI instance"""
        response = await self._send_request("workspace/callTool", {
            "name": "pdf",
            "arguments": {
                "url": url,
            }
        })
        
        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "url": url
            }
        
        try:
            # Parse the content from the response
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                result = json.loads(content[0].get("text", "{}"))
                return result
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "url": url
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting PDF: {str(e)}",
                "traceback": traceback.format_exc(),
                "url": url
            }
    
    async def execute_js(self, url: str, js_code: List[str]):
        """Execute JavaScript on a URL using the remote Crawl4AI instance"""
        response = await self._send_request("workspace/callTool", {
            "name": "execute_js",
            "arguments": {
                "url": url,
                "js_code": js_code,
            }
        })
        
        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "url": url
            }
        
        try:
            # Parse the content from the response
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                result = json.loads(content[0].get("text", "{}"))
                return result
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "url": url
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing JavaScript: {str(e)}",
                "traceback": traceback.format_exc(),
                "url": url
            }
    
    async def get_html(self, url: str):
        """Get the HTML of a URL using the remote Crawl4AI instance"""
        response = await self._send_request("workspace/callTool", {
            "name": "html",
            "arguments": {
                "url": url,
            }
        })
        
        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "url": url
            }
        
        try:
            # Parse the content from the response
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                result = json.loads(content[0].get("text", "{}"))
                return result
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "url": url
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting HTML: {str(e)}",
                "traceback": traceback.format_exc(),
                "url": url
            }
    
    async def ask_question(self, query: str):
        """Ask a question about Crawl4AI using the remote instance"""
        response = await self._send_request("workspace/callTool", {
            "name": "ask",
            "arguments": {
                "query": query,
            }
        })
        
        if "error" in response:
            return {
                "success": False,
                "error": response["error"],
                "query": query
            }
        
        try:
            # Parse the content from the response
            content = response.get("result", {}).get("content", [])
            if content and len(content) > 0:
                result = json.loads(content[0].get("text", "{}"))
                return result
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "query": query
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error asking question: {str(e)}",
                "traceback": traceback.format_exc(),
                "query": query
            }

# Global client instance
client = Crawl4AIClient()

# Gradio interface functions
async def crawl_interface(url, css_selector, word_count, extract_links, extract_media):
    """Gradio interface function for crawling a URL"""
    if not url.strip():
        return "Please enter a URL", "", "", "", ""
    
    try:
        result = await client.crawl_url(url, css_selector, word_count)
        return format_result(result, extract_links, extract_media)
    except Exception as e:
        error_msg = f"Interface error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg, "", "", "", ""

def format_result(result: Dict[str, Any], show_links: bool, show_media: bool) -> tuple:
    """Format the crawl result for Gradio display"""
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        if "traceback" in result:
            error_msg += f"\n\nTraceback:\n{result['traceback']}"
        return error_msg, "", "", "", ""
    
    # Format basic info
    info = f"""
**URL:** {result.get('url', 'N/A')}
**Title:** {result.get('title', 'N/A')}
**Success:** ✅ {result.get('success', False)}
**Word Count:** {result.get('word_count', 0)}
**Timestamp:** {result.get('timestamp', datetime.now().isoformat())}
"""
    
    # Get markdown content
    markdown = result.get('markdown', '')
    
    # Format links
    links_info = ""
    if show_links and result.get('links'):
        internal_links = result['links'].get('internal', [])
        external_links = result['links'].get('external', [])
        links_info = f"**Internal Links:** {len(internal_links)} | **External Links:** {len(external_links)}\n\n"
        
        if internal_links:
            links_info += "### 🔗 Internal Links\n"
            for i, link in enumerate(internal_links[:20], 1):  # Limit to first 20
                text = link.get('text', 'No text')[:100]  # Limit text length
                href = link.get('href', '#')
                links_info += f"{i}. [{text}]({href})\n"
        
        if external_links:
            links_info += "\n### 🌐 External Links\n"
            for i, link in enumerate(external_links[:20], 1):  # Limit to first 20
                text = link.get('text', 'No text')[:100]  # Limit text length
                href = link.get('href', '#')
                links_info += f"{i}. [{text}]({href})\n"
    
    # Format media info
    media_info = ""
    if show_media and result.get('media'):
        images = result['media'].get('images', [])
        videos = result['media'].get('videos', [])
        media_info = f"**Images:** {len(images)} | **Videos:** {len(videos)}\n\n"
        
        if images:
            media_info += "### 🖼️ Images\n"
            for i, img in enumerate(images[:10], 1):  # Limit to first 10
                alt = img.get('alt', 'No alt text')[:100]
                src = img.get('src', '#')
                media_info += f"{i}. ![{alt}]({src})\n"
        
        if videos:
            media_info += "\n### 🎥 Videos\n"
            for i, video in enumerate(videos[:10], 1):  # Limit to first 10
                title = video.get('title', 'No title')[:100]
                src = video.get('src', '#')
                media_info += f"{i}. [{title}]({src})\n"
    
    # Format metadata
    metadata_info = ""
    if result.get('metadata'):
        metadata = result['metadata']
        if 'description' in metadata:
            metadata_info += f"**Description:** {metadata['description']}\n\n"
        
        headings = metadata.get('headings', [])
        if headings:
            metadata_info += "### 📋 Page Structure\n"
            for heading in headings[:10]:  # Limit to first 10
                level = heading.get('level', 1)
                text = heading.get('text', '')[:100]
                indent = "  " * (level - 1)
                metadata_info += f"{indent}- H{level}: {text}\n"
    
    return info, markdown, links_info, media_info, metadata_info

async def screenshot_interface(url, wait_time):
    """Gradio interface function for getting a screenshot"""
    if not url.strip():
        return "Please enter a URL", None
    
    try:
        result = await client.get_screenshot(url, wait_time)
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            if "traceback" in result:
                error_msg += f"\n\nTraceback:\n{result['traceback']}"
            return error_msg, None
        
        # Decode the base64 image
        screenshot_data = result.get("screenshot", "")
        if not screenshot_data:
            return "No screenshot data returned", None
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(base64.b64decode(screenshot_data))
            tmp_path = tmp.name
        
        return f"Screenshot of {url} captured successfully", tmp_path
    except Exception as e:
        error_msg = f"Screenshot error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg, None

async def pdf_interface(url):
    """Gradio interface function for getting a PDF"""
    if not url.strip():
        return "Please enter a URL", None
    
    try:
        result = await client.get_pdf(url)
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            if "traceback" in result:
                error_msg += f"\n\nTraceback:\n{result['traceback']}"
            return error_msg, None
        
        # Decode the base64 PDF
        pdf_data = result.get("pdf", "")
        if not pdf_data:
            return "No PDF data returned", None
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(base64.b64decode(pdf_data))
            tmp_path = tmp.name
        
        return f"PDF of {url} generated successfully", tmp_path
    except Exception as e:
        error_msg = f"PDF error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg, None

async def js_interface(url, js_code):
    """Gradio interface function for executing JavaScript"""
    if not url.strip():
        return "Please enter a URL", ""
    
    if not js_code.strip():
        return "Please enter JavaScript code", ""
    
    try:
        # Split the JS code into lines
        js_lines = [line.strip() for line in js_code.split("\n") if line.strip()]
        
        result = await client.execute_js(url, js_lines)
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            if "traceback" in result:
                error_msg += f"\n\nTraceback:\n{result['traceback']}"
            return error_msg, ""
        
        # Return the HTML result
        html_content = result.get("html", "")
        return f"JavaScript executed successfully on {url}", html_content
    except Exception as e:
        error_msg = f"JavaScript execution error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg, ""

async def html_interface(url):
    """Gradio interface function for getting HTML"""
    if not url.strip():
        return "Please enter a URL", ""
    
    try:
        result = await client.get_html(url)
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            if "traceback" in result:
                error_msg += f"\n\nTraceback:\n{result['traceback']}"
            return error_msg, ""
        
        # Return the HTML result
        html_content = result.get("html", "")
        return f"HTML retrieved successfully from {url}", html_content
    except Exception as e:
        error_msg = f"HTML retrieval error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg, ""

async def ask_interface(query):
    """Gradio interface function for asking questions"""
    if not query.strip():
        return "Please enter a question"
    
    try:
        result = await client.ask_question(query)
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error")
            if "traceback" in result:
                error_msg += f"\n\nTraceback:\n{result['traceback']}"
            return error_msg
        
        # Return the answer
        answer = result.get("answer", "No answer provided")
        return answer
    except Exception as e:
        error_msg = f"Question answering error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg

async def check_connection():
    """Check connection to the Crawl4AI server"""
    try:
        tools = await client.list_tools()
        if "error" in tools:
            return f"❌ Connection failed: {tools['error']}"
        
        tool_names = [t["name"] for t in tools.get("tools", [])]
        return f"✅ Connected to Crawl4AI server\nAvailable tools: {', '.join(tool_names)}"
    except Exception as e:
        return f"❌ Connection failed: {str(e)}"

# Create Gradio interface
def create_interface():
    with gr.Blocks(title="Crawl4AI - Remote API Client", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🚀🤖 Crawl4AI: Remote API Client
        
        Connect to a remote Crawl4AI instance and access its API endpoints.
        
        **Features:**
        - 📄 Extract clean content from any webpage
        - 📸 Capture screenshots of websites
        - 📑 Generate PDFs of web pages
        - 🔍 Execute JavaScript on web pages
        - 🌐 Retrieve raw HTML content
        - 💬 Ask questions about Crawl4AI
        """)
        
        with gr.Row():
            with gr.Column():
                connection_status = gr.Textbox(
                    label="🔌 Connection Status",
                    value="Checking connection...",
                    interactive=False
                )
                
                check_btn = gr.Button("🔄 Check Connection", variant="secondary")
                check_btn.click(fn=check_connection, outputs=connection_status)
        
        with gr.Tabs() as tabs:
            # Tab 1: Content Extraction
            with gr.TabItem("📄 Content Extraction"):
                with gr.Row():
                    with gr.Column(scale=2):
                        url_input = gr.Textbox(
                            label="🌐 URL to Scrape",
                            placeholder="https://example.com or example.com",
                            value="https://docs.crawl4ai.com/first-steps/introduction"
                        )
                        
                        with gr.Row():
                            extract_links_check = gr.Checkbox(label="🔗 Extract Links", value=True)
                            extract_media_check = gr.Checkbox(label="🖼️ Extract Media", value=True)
                        
                        with gr.Accordion("⚙️ Advanced Options", open=False):
                            css_selector = gr.Textbox(
                                label="🎯 CSS Selector (optional)",
                                placeholder="article, .content, #main, .post-body",
                                info="Target specific elements on the page"
                            )
                            
                            word_count = gr.Slider(
                                minimum=0,
                                maximum=50,
                                value=5,
                                step=1,
                                label="📝 Minimum Word Count per Line",
                                info="Filter out lines with fewer words (0 = no filter)"
                            )
                        
                        crawl_btn = gr.Button("🚀 Extract Content", variant="primary", size="lg")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        ### 💡 Tips:
                        - **Remote Processing**: Content is processed by the Crawl4AI server
                        - **CSS Selectors**: Target specific content areas
                        - **Word Filter**: Remove short/empty lines
                        - **Link Analysis**: Discover site structure
                        
                        ### 🎯 Example Selectors:
                        - `article` - Main article content
                        - `.content` - Elements with 'content' class
                        - `#main` - Element with 'main' ID
                        - `h1, h2, h3` - All headings
                        - `.post-body p` - Paragraphs in post body
                        """)
                
                # Output sections
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
                            placeholder="Scraped content will appear here..."
                        )
                    
                    with gr.TabItem("🔗 Links Analysis"):
                        links_output = gr.Markdown(
                            label="Links Found",
                            value="Enable 'Extract Links' and scrape a page to see links here."
                        )
                        
                    with gr.TabItem("🖼️ Media Elements"):
                        media_output = gr.Markdown(
                            label="Media Elements",
                            value="Enable 'Extract Media' and scrape a page to see media here."
                        )
                        
                    with gr.TabItem("📊 Metadata"):
                        metadata_output = gr.Markdown(
                            label="Page Metadata",
                            value="Page structure and metadata will appear here."
                        )
                
                # Connect the interface
                crawl_btn.click(
                    fn=crawl_interface,
                    inputs=[url_input, css_selector, word_count, extract_links_check, extract_media_check],
                    outputs=[info_output, markdown_output, links_output, media_output, metadata_output]
                )
            
            # Tab 2: Screenshots
            with gr.TabItem("📸 Screenshots"):
                with gr.Row():
                    with gr.Column():
                        screenshot_url = gr.Textbox(
                            label="🌐 URL to Screenshot",
                            placeholder="https://example.com",
                            value="https://docs.crawl4ai.com"
                        )
                        
                        wait_time = gr.Slider(
                            minimum=0.1,
                            maximum=10.0,
                            value=1.0,
                            step=0.1,
                            label="⏱️ Wait Time (seconds)",
                            info="Time to wait after page load before taking screenshot"
                        )
                        
                        screenshot_btn = gr.Button("📸 Capture Screenshot", variant="primary")
                
                with gr.Row():
                    with gr.Column():
                        screenshot_status = gr.Textbox(label="Status", interactive=False)
                        screenshot_output = gr.Image(label="Screenshot", type="filepath")
                
                # Connect the interface
                screenshot_btn.click(
                    fn=screenshot_interface,
                    inputs=[screenshot_url, wait_time],
                    outputs=[screenshot_status, screenshot_output]
                )
            
            # Tab 3: PDF Generation
            with gr.TabItem("📑 PDF Generation"):
                with gr.Row():
                    with gr.Column():
                        pdf_url = gr.Textbox(
                            label="🌐 URL to Convert to PDF",
                            placeholder="https://example.com",
                            value="https://docs.crawl4ai.com"
                        )
                        
                        pdf_btn = gr.Button("📑 Generate PDF", variant="primary")
                
                with gr.Row():
                    with gr.Column():
                        pdf_status = gr.Textbox(label="Status", interactive=False)
                        pdf_output = gr.File(label="Generated PDF")
                
                # Connect the interface
                pdf_btn.click(
                    fn=pdf_interface,
                    inputs=[pdf_url],
                    outputs=[pdf_status, pdf_output]
                )
            
            # Tab 4: JavaScript Execution
            with gr.TabItem("🔍 JavaScript Execution"):
                with gr.Row():
                    with gr.Column():
                        js_url = gr.Textbox(
                            label="🌐 URL for JavaScript Execution",
                            placeholder="https://example.com",
                            value="https://news.ycombinator.com"
                        )
                        
                        js_code = gr.Textbox(
                            label="📝 JavaScript Code",
                            placeholder="await page.click('a.morelink')\nawait page.waitForTimeout(1000)",
                            lines=5,
                            value="await page.click('a.morelink')\nawait page.waitForTimeout(1000)"
                        )
                        
                        js_btn = gr.Button("▶️ Execute JavaScript", variant="primary")
                
                with gr.Row():
                    with gr.Column():
                        js_status = gr.Textbox(label="Status", interactive=False)
                        js_output = gr.Textbox(
                            label="HTML Result",
                            lines=15,
                            show_copy_button=True
                        )
                
                # Connect the interface
                js_btn.click(
                    fn=js_interface,
                    inputs=[js_url, js_code],
                    outputs=[js_status, js_output]
                )
            
            # Tab 5: HTML Retrieval
            with gr.TabItem("🌐 HTML Retrieval"):
                with gr.Row():
                    with gr.Column():
                        html_url = gr.Textbox(
                            label="🌐 URL to Retrieve HTML",
                            placeholder="https://example.com",
                            value="https://docs.crawl4ai.com"
                        )
                        
                        html_btn = gr.Button("🌐 Get HTML", variant="primary")
                
                with gr.Row():
                    with gr.Column():
                        html_status = gr.Textbox(label="Status", interactive=False)
                        html_output = gr.Textbox(
                            label="HTML Content",
                            lines=15,
                            show_copy_button=True
                        )
                
                # Connect the interface
                html_btn.click(
                    fn=html_interface,
                    inputs=[html_url],
                    outputs=[html_status, html_output]
                )
            
            # Tab 6: Ask Questions
            with gr.TabItem("💬 Ask Questions"):
                with gr.Row():
                    with gr.Column():
                        question_input = gr.Textbox(
                            label="❓ Question about Crawl4AI",
                            placeholder="How do I extract internal links when crawling a page?",
                            lines=3,
                            value="How do I extract internal links when crawling a page?"
                        )
                        
                        ask_btn = gr.Button("🔍 Ask Question", variant="primary")
                
                with gr.Row():
                    with gr.Column():
                        answer_output = gr.Markdown(
                            label="Answer",
                            value="Ask a question to get an answer from the Crawl4AI documentation."
                        )
                
                # Connect the interface
                ask_btn.click(
                    fn=ask_interface,
                    inputs=[question_input],
                    outputs=[answer_output]
                )
        
        # Examples
        with gr.Accordion("📚 Examples", open=False):
            gr.Examples(
                examples=[
                    ["https://docs.crawl4ai.com/first-steps/introduction", "", 5, True, True],
                    ["https://news.ycombinator.com", ".storylink", 3, True, False],
                    ["https://github.com/unclecode/crawl4ai", "article, .markdown-body", 10, False, False],
                    ["https://python.org", ".main-content", 5, True, True],
                    ["https://example.com", "", 0, True, True],
                ],
                inputs=[url_input, css_selector, word_count, extract_links_check, extract_media_check],
                label="📚 Try these examples:"
            )
        
        gr.Markdown("""
        ---
        ### 🔧 Technical Details
        
        This application connects to a remote Crawl4AI instance using the MCP protocol:
        - **WebSocket Connection**: Real-time communication with the Crawl4AI server
        - **MCP Protocol**: Standardized messaging for tool invocation
        - **Remote Processing**: All web crawling happens on the server
        - **API Endpoints**: Access to all Crawl4AI features through a unified interface
        
        ### 🚀 Full Crawl4AI Features
        
        For more information about Crawl4AI:
        - **GitHub**: [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
        - **Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
        - **Python Package**: `pip install crawl4ai`
        
        **Built with ❤️ by the Crawl4AI community**
        """)
        
        # Run connection check on startup
        demo.load(fn=check_connection, outputs=connection_status)
    
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