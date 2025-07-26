---
title: Crawl4AI Web Crawler
emoji: 🚀🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Open-source LLM Friendly Web Crawler & Scraper
---

# 🚀🤖 Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper

Crawl4AI is a powerful, open-source web crawler and scraper designed specifically for Large Language Models (LLMs) and AI applications. This Hugging Face Space provides a user-friendly interface to crawl websites, extract content, and generate clean markdown output.

## ✨ Features

- **🔥 LLM-Ready Output**: Generates clean, structured markdown perfect for RAG and fine-tuning
- **⚡ Lightning Fast**: Optimized for speed and efficiency
- **🎯 Smart Extraction**: CSS selectors, custom prompts, and intelligent content filtering
- **📸 Visual Capture**: Full-page screenshots and PDF generation
- **🔗 Link Analysis**: Comprehensive internal and external link extraction
- **🤖 AI-Powered**: Optional LLM-based extraction with custom prompts

## 🚀 Quick Start

1. **Enter a URL** in the input field
2. **Choose extraction type**:
   - **Markdown**: Clean, readable content extraction
   - **Structured**: Data-focused extraction with chunking
   - **LLM**: AI-powered extraction with custom prompts
3. **Configure options** (optional):
   - CSS selectors for targeted extraction
   - Screenshots and PDF generation
   - Word count thresholds
4. **Click "Crawl Website"** and get results!

## 💡 Use Cases

- **📚 Content Research**: Extract articles, documentation, and web content
- **🔍 Data Collection**: Gather structured data from websites
- **📊 Market Research**: Analyze competitor websites and content
- **🤖 AI Training**: Generate training data for language models
- **📖 Documentation**: Convert web content to markdown for documentation

## 🛠️ Advanced Features

### CSS Selectors
Target specific elements on a page:
```
article.main-content
.post-body
#content-area
```

### LLM Extraction
Use custom prompts for specific data extraction:
```
Extract all product names, prices, and descriptions from this e-commerce page
```

### Screenshots & PDFs
Capture visual content and generate downloadable files for archival purposes.

## 🔧 Technical Details

This Space runs a simplified version of Crawl4AI optimized for Hugging Face Spaces constraints:

- **Browser**: Headless Chromium with optimized flags and automatic installation
- **Memory**: Efficient memory management for HF Spaces limits
- **Security**: Sandboxed execution environment
- **Performance**: Single-process mode for stability
- **Reliability**: Automatic browser installation and recovery on startup

### Browser Installation
The Space automatically handles Playwright browser installation:
- Browsers are installed during container build
- Runtime verification ensures browsers are available
- Automatic recovery if browsers are missing
- Optimized for HuggingFace Spaces environment

## 🌟 Full Crawl4AI Features

For the complete Crawl4AI experience with advanced features, check out:

- **GitHub Repository**: [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- **Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
- **Docker Deployment**: Full-featured API server
- **Python Package**: `pip install crawl4ai`

## 📝 Examples

### Basic Web Scraping
```python
from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    print(result.markdown)
```

### Advanced Extraction
```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy

strategy = LLMExtractionStrategy(
    provider="openai/gpt-4",
    instruction="Extract product information"
)

result = await crawler.arun(
    url="https://shop.example.com",
    extraction_strategy=strategy
)
```

## 🤝 Contributing

Crawl4AI is open-source and welcomes contributions! Visit our [GitHub repository](https://github.com/unclecode/crawl4ai) to:

- Report issues
- Submit pull requests
- Request features
- Join the community

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](https://github.com/unclecode/crawl4ai/blob/main/LICENSE) file for details.

---

**Built with ❤️ by the Crawl4AI community**