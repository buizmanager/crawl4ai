# Crawl4AI API Endpoints Documentation

This document provides detailed information about the API endpoints available in the Crawl4AI server.

## Base URL

All API endpoints are relative to the base URL of your Hugging Face Space:

```
https://your-space-name.hf.space
```

## Authentication

Currently, the API does not require authentication. However, rate limiting is applied to prevent abuse.

## Endpoints

### Health Check

```
GET /health
```

Returns the current status of the server.

**Response:**

```json
{
  "status": "ok",
  "timestamp": 1625097600
}
```

### Convert Webpage to Markdown

```
POST /md
```

Converts a webpage to markdown format.

**Request Body:**

```json
{
  "url": "https://example.com",
  "f": "main",  // Optional filter
  "q": "search term",  // Optional query
  "c": true  // Optional cache flag
}
```

**Response:**

```json
{
  "url": "https://example.com",
  "filter": "main",
  "query": "search term",
  "cache": true,
  "markdown": "# Example Domain\n\nThis domain is...",
  "success": true
}
```

### Get Processed HTML

```
POST /html
```

Crawls the URL and returns the processed HTML.

**Request Body:**

```json
{
  "url": "https://example.com"
}
```

**Response:**

```json
{
  "html": "<!DOCTYPE html><html>...</html>",
  "url": "https://example.com",
  "success": true
}
```

### Capture Screenshot

```
POST /screenshot
```

Captures a screenshot of the specified URL.

**Request Body:**

```json
{
  "url": "https://example.com",
  "screenshot_wait_for": "networkidle",  // Optional
  "output_path": "/tmp/screenshot.png"  // Optional
}
```

**Response (with output_path):**

```json
{
  "success": true,
  "path": "/tmp/screenshot.png"
}
```

**Response (without output_path):**

```json
{
  "success": true,
  "screenshot": "base64-encoded-image-data"
}
```

### Generate PDF

```
POST /pdf
```

Generates a PDF of the specified URL.

**Request Body:**

```json
{
  "url": "https://example.com",
  "output_path": "/tmp/document.pdf"  // Optional
}
```

**Response (with output_path):**

```json
{
  "success": true,
  "path": "/tmp/document.pdf"
}
```

**Response (without output_path):**

```json
{
  "success": true,
  "pdf": "base64-encoded-pdf-data"
}
```

### Execute JavaScript

```
POST /execute_js
```

Executes JavaScript on the specified URL.

**Request Body:**

```json
{
  "url": "https://example.com",
  "scripts": [
    "document.title",
    "Array.from(document.querySelectorAll('a')).map(a => a.href)"
  ]
}
```

**Response:**

```json
{
  "url": "https://example.com",
  "html": "<!DOCTYPE html><html>...</html>",
  "success": true,
  "js_execution_result": {
    "results": [
      "Example Domain",
      ["https://www.iana.org/domains/example"]
    ]
  },
  // ... other CrawlResult fields
}
```

### Crawl Multiple URLs

```
POST /crawl
```

Crawls multiple URLs and returns comprehensive results.

**Request Body:**

```json
{
  "urls": ["https://example.com", "https://example.org"],
  "browser_config": {
    "headless": true,
    "text_mode": true
  },
  "crawler_config": {
    "simulate_user": true,
    "extract_metadata": true
  }
}
```

**Response:**

```json
[
  {
    "url": "https://example.com",
    "html": "<!DOCTYPE html><html>...</html>",
    "success": true,
    // ... other CrawlResult fields
  },
  {
    "url": "https://example.org",
    "html": "<!DOCTYPE html><html>...</html>",
    "success": true,
    // ... other CrawlResult fields
  }
]
```

## MCP Endpoints

### WebSocket Endpoint

```
WebSocket /mcp/ws
```

WebSocket endpoint for MCP (Model Control Protocol).

### Server-Sent Events Endpoint

```
GET /mcp/sse
```

Server-Sent Events endpoint for MCP.

### Schema Endpoint

```
GET /mcp/schema
```

Returns the JSON Schema for available MCP tools and resources.

**Response:**

```json
{
  "tools": [
    {
      "name": "md",
      "description": "Convert a webpage to markdown format",
      "inputSchema": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string",
            "description": "URL to crawl"
          },
          // ... other properties
        },
        "required": ["url"]
      }
    },
    // ... other tools
  ],
  "resources": [],
  "resource_templates": []
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error responses include a JSON body with details:

```json
{
  "detail": "Error message"
}
```