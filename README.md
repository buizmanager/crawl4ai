# Crawl4AI API Endpoint for Hugging Face Spaces

This repository contains the necessary files to deploy the Crawl4AI server on Hugging Face Spaces, providing a powerful web crawling and scraping API that is LLM-friendly.

## Features

- **Full Crawl4AI Server**: Runs the complete Crawl4AI server with all its capabilities
- **API Endpoints**: Exposes all the core API endpoints for remote access
- **MCP Server**: Includes MCP (Model Control Protocol) server endpoints for integration with LLMs
- **Optimized for Hugging Face Spaces**: Configured to run efficiently within the Hugging Face Spaces environment

## API Endpoints

The following API endpoints are available:

- **`/md`**: Convert a webpage to markdown format
- **`/html`**: Get processed HTML from a webpage
- **`/screenshot`**: Capture a screenshot of a webpage
- **`/pdf`**: Generate a PDF of a webpage
- **`/execute_js`**: Execute JavaScript on a webpage
- **`/crawl`**: Crawl multiple URLs and get comprehensive results

## MCP Server Endpoints

MCP (Model Control Protocol) endpoints are available at:

- **`/mcp/ws`**: WebSocket endpoint for MCP
- **`/mcp/sse`**: Server-Sent Events endpoint for MCP
- **`/mcp/schema`**: JSON Schema for available MCP tools and resources

## Environment Variables

The following environment variables can be configured:

- **`OPENAI_API_KEY`**: OpenAI API key for LLM integration
- **`DEEPSEEK_API_KEY`**: DeepSeek API key
- **`ANTHROPIC_API_KEY`**: Anthropic API key
- **`GROQ_API_KEY`**: Groq API key
- **`TOGETHER_API_KEY`**: Together API key
- **`MISTRAL_API_KEY`**: Mistral API key
- **`GEMINI_API_TOKEN`**: Google Gemini API token

## Usage

### Basic Request Example

```python
import requests

# Convert a webpage to markdown
response = requests.post(
    "https://your-space-name.hf.space/md",
    json={"url": "https://example.com"}
)
print(response.json())

# Take a screenshot of a webpage
response = requests.post(
    "https://your-space-name.hf.space/screenshot",
    json={"url": "https://example.com"}
)
screenshot_data = response.json()["screenshot"]
```

### MCP Integration Example

```python
from mcp.client import Client

# Connect to the MCP server
client = Client("wss://your-space-name.hf.space/mcp/ws")
await client.initialize()

# List available tools
tools = await client.list_tools()
print(tools)

# Call a tool
result = await client.call_tool("md", {"url": "https://example.com"})
print(result)
```

## Deployment

This repository is designed to be deployed directly to Hugging Face Spaces. The deployment process is handled automatically by Hugging Face's infrastructure.

## Configuration

The server configuration is defined in `config.yml`. You can modify this file to adjust various settings such as:

- Rate limiting
- Security settings
- Browser configuration
- Redis configuration
- Logging levels

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgements

- [Crawl4AI](https://github.com/buizmanager/crawl4ai) - The core library powering this API
- [Hugging Face Spaces](https://huggingface.co/spaces) - The hosting platform
- [MCP](https://github.com/microsoft/mcp) - Model Control Protocol for LLM integration