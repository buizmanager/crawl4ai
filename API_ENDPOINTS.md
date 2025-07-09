# 🚀 Crawl4AI API Endpoints

This document describes the API endpoints available through the Crawl4AI MCP server.

## 📋 MCP Protocol

The Crawl4AI server uses the MCP (Model Control Protocol) to expose its functionality. This protocol provides a standardized way to invoke tools and receive responses.

### Connection Methods

- **WebSocket**: `ws://server-address:11235/mcp/ws`
- **Server-Sent Events (SSE)**: `http://server-address:11235/mcp/sse`

## 🔧 Available Tools

The following tools are available through the MCP server:

### 1. `md` - Markdown Extraction

Extracts clean, structured markdown content from a URL.

**Parameters:**
- `url` (string): The URL to extract content from
- `f` (string, optional): Format type - "fit", "raw", "bm25", or "llm"
- `q` (string, optional): CSS selector for targeting specific content
- `c` (string, optional): Minimum word count threshold

**Example:**
```json
{
  "url": "https://example.com",
  "f": "fit",
  "q": "article.main-content",
  "c": "5"
}
```

### 2. `screenshot` - Screenshot Capture

Captures a screenshot of a URL.

**Parameters:**
- `url` (string): The URL to capture
- `screenshot_wait_for` (number, optional): Time to wait after page load before capturing (in seconds)

**Example:**
```json
{
  "url": "https://example.com",
  "screenshot_wait_for": 1.0
}
```

### 3. `pdf` - PDF Generation

Generates a PDF of a URL.

**Parameters:**
- `url` (string): The URL to convert to PDF

**Example:**
```json
{
  "url": "https://example.com"
}
```

### 4. `execute_js` - JavaScript Execution

Executes JavaScript code on a URL.

**Parameters:**
- `url` (string): The URL to execute JavaScript on
- `js_code` (array of strings): JavaScript code to execute

**Example:**
```json
{
  "url": "https://news.ycombinator.com/news",
  "js_code": [
    "await page.click('a.morelink')",
    "await page.waitForTimeout(1000)"
  ]
}
```

### 5. `html` - HTML Retrieval

Retrieves the HTML content of a URL.

**Parameters:**
- `url` (string): The URL to retrieve HTML from

**Example:**
```json
{
  "url": "https://example.com"
}
```

### 6. `ask` - Question Answering

Asks a question about Crawl4AI and gets an answer.

**Parameters:**
- `query` (string): The question to ask

**Example:**
```json
{
  "query": "How do I extract internal links when crawling a page?"
}
```

### 7. `crawl` - Multi-URL Crawling

Crawls multiple URLs and extracts content.

**Parameters:**
- `urls` (array of strings): The URLs to crawl
- `browser_config` (object, optional): Browser configuration options
- `crawler_config` (object, optional): Crawler configuration options

**Example:**
```json
{
  "urls": ["https://example.com", "https://example.org"],
  "browser_config": {},
  "crawler_config": {}
}
```

## 🔌 Using the API with Python

Here's an example of how to use the API with Python:

```python
import asyncio
from mcp.client.websocket import websocket_client
from mcp.client.session import ClientSession
import json

async def main():
    # Connect to the MCP server
    async with websocket_client("ws://localhost:11235/mcp/ws") as (reader, writer):
        # Create a client session
        async with ClientSession(reader, writer) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools_response = await session.list_tools()
            print("Available tools:", [t.name for t in tools_response.tools])
            
            # Extract markdown from a URL
            md_response = await session.call_tool(
                "md",
                {
                    "url": "https://example.com",
                    "f": "fit",
                    "q": None,
                    "c": "0",
                },
            )
            
            # Parse the response
            result = json.loads(md_response.content[0].text)
            print("Markdown:", result['markdown'][:100], "...")

# Run the async function
asyncio.run(main())
```

## 🔍 Response Format

All API responses follow a standard format:

```json
{
  "success": true,
  "url": "https://example.com",
  "title": "Example Domain",
  "markdown": "# Example Domain\n\nThis domain is...",
  "word_count": 42,
  "timestamp": "2023-07-09T12:34:56.789Z",
  "links": {
    "internal": [...],
    "external": [...]
  },
  "media": {
    "images": [...],
    "videos": [...]
  },
  "metadata": {...}
}
```

## 🛠️ Error Handling

If an error occurs, the response will include:

```json
{
  "success": false,
  "error": "Error message",
  "traceback": "Detailed error traceback"
}
```

## 📚 Additional Resources

- **Crawl4AI Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
- **MCP Protocol Documentation**: [mcp-sdk Documentation](https://github.com/unclecode/mcp-sdk)
- **GitHub Repository**: [github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)

---

**Built with ❤️ by the Crawl4AI community**