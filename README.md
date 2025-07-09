# Crawl4AI API for Hugging Face Spaces

This repository contains the necessary files to deploy the Crawl4AI API on Hugging Face Spaces, providing a powerful web crawling and scraping API with a user-friendly interface.

## Features

- **Interactive UI**: Gradio-based interface for testing the API directly in your browser
- **REST API Endpoints**: Full access to Crawl4AI functionality via REST API
- **Optimized for Hugging Face Spaces**: Simplified deployment that works reliably on Hugging Face Spaces

## Interactive UI

The Hugging Face Space includes an interactive UI that allows you to:

- Convert webpages to markdown
- Take screenshots of webpages
- Execute JavaScript on webpages

Simply enter a URL and click the corresponding button to see the results.

## API Endpoints

The following REST API endpoints are available:

- **`/md`**: Convert a webpage to markdown format
- **`/html`**: Get processed HTML from a webpage
- **`/screenshot`**: Capture a screenshot of a webpage
- **`/pdf`**: Generate a PDF of a webpage
- **`/execute_js`**: Execute JavaScript on a webpage
- **`/crawl`**: Crawl multiple URLs and get comprehensive results

## Usage Examples

### Using the REST API

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

### API Request Examples

#### Convert to Markdown

```json
POST /md
{
  "url": "https://example.com"
}
```

#### Take Screenshot

```json
POST /screenshot
{
  "url": "https://example.com",
  "screenshot_wait_for": "networkidle"
}
```

#### Execute JavaScript

```json
POST /execute_js
{
  "url": "https://example.com",
  "scripts": ["document.title", "Array.from(document.querySelectorAll('a')).map(a => a.href)"]
}
```

## Deployment

This repository is designed to be deployed directly to Hugging Face Spaces. The deployment process is handled automatically by Hugging Face's infrastructure.

## Configuration

The server configuration is defined in `config.yml`. You can modify this file to adjust various settings such as:

- Browser configuration
- Logging levels
- Server port and host

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Acknowledgements

- [Crawl4AI](https://github.com/buizmanager/crawl4ai) - The core library powering this API
- [Hugging Face Spaces](https://huggingface.co/spaces) - The hosting platform
- [Gradio](https://gradio.app/) - The UI framework used for the interactive interface