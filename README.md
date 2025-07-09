---
title: Crawl4AI Remote API Client
emoji: 🚀🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Remote API client for Crawl4AI and MCP-server
---

# 🚀🤖 Crawl4AI: Remote API Client

This Hugging Face Space provides a user-friendly interface to connect to a remote Crawl4AI instance and access its API endpoints. It allows you to use all the powerful features of Crawl4AI without having to install it locally.

## ✨ Features

- **🔌 Remote Connection**: Connect to any Crawl4AI server using the MCP protocol
- **📄 Content Extraction**: Extract clean, structured markdown from any webpage
- **📸 Screenshots**: Capture full-page screenshots of websites
- **📑 PDF Generation**: Convert web pages to downloadable PDFs
- **🔍 JavaScript Execution**: Run custom JavaScript on web pages
- **🌐 HTML Retrieval**: Get the raw HTML content of any webpage
- **💬 Question Answering**: Ask questions about Crawl4AI and get answers

## 🚀 Quick Start

1. **Set up a Crawl4AI server**:
   - Install and run the Crawl4AI Docker image on your server
   - Make sure the MCP server endpoint is accessible

2. **Configure this client**:
   - Set the `CRAWL4AI_API_URL` environment variable to your server's WebSocket URL
   - Example: `ws://your-server-ip:11235/mcp/ws`

3. **Use the interface**:
   - Check the connection status to verify connectivity
   - Use any of the available tools to interact with the Crawl4AI server

## 🔧 Configuration

### Environment Variables

Set these in your Hugging Face Space settings:

- `CRAWL4AI_API_URL`: WebSocket URL of your Crawl4AI server (default: `ws://localhost:11235/mcp/ws`)
- `MCP_SERVER_URL`: Alternative URL for the MCP server (if different from CRAWL4AI_API_URL)

## 💡 Use Cases

- **📚 Content Research**: Extract articles, documentation, and web content
- **🔍 Data Collection**: Gather structured data from websites
- **📊 Market Research**: Analyze competitor websites and content
- **🤖 AI Training**: Generate training data for language models
- **📖 Documentation**: Convert web content to markdown for documentation

## 🛠️ Technical Details

### WebSocket Communication

This client uses WebSocket communication with JSON-RPC messages to interact with the Crawl4AI server:

- **WebSocket Transport**: Real-time bidirectional communication
- **JSON-RPC Messages**: Standardized message format
- **Tool Invocation**: Remote execution of Crawl4AI tools
- **Streaming Results**: Efficient handling of large responses

### Available Tools

The following tools are available through the MCP server:

- **md**: Extract markdown content from a URL
- **screenshot**: Capture a screenshot of a URL
- **pdf**: Generate a PDF of a URL
- **execute_js**: Execute JavaScript on a URL
- **html**: Get the HTML content of a URL
- **ask**: Ask questions about Crawl4AI

## 🔌 Setting Up Your Own Crawl4AI Server

To set up your own Crawl4AI server:

1. **Install Docker** on your server

2. **Pull the Crawl4AI image**:
   ```bash
   docker pull unclecode/crawl4ai:latest
   ```

3. **Run the container**:
   ```bash
   docker run -d --name crawl4ai -p 11235:11235 unclecode/crawl4ai:latest
   ```

4. **Configure this client** to connect to your server:
   - Set `CRAWL4AI_API_URL` to `ws://your-server-ip:11235/mcp/ws`

## 🤝 Contributing

Crawl4AI is open-source and welcomes contributions! Visit the [GitHub repository](https://github.com/unclecode/crawl4ai) to:

- Report issues
- Submit pull requests
- Request features
- Join the community

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](https://github.com/unclecode/crawl4ai/blob/main/LICENSE) file for details.

---

**Built with ❤️ by the Crawl4AI community**