# 🚀 Crawl4AI Remote API Client Setup Guide

This guide will help you set up the Crawl4AI Remote API Client to connect to a remote Crawl4AI server.

## 📋 Prerequisites

1. **Docker**: Install Docker on your server
   - [Docker Installation Guide](https://docs.docker.com/get-docker/)

2. **Docker Compose**: Install Docker Compose
   - [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)

3. **Server with sufficient resources**:
   - At least 4GB RAM
   - At least 10GB free disk space
   - Internet connectivity

## 🎯 Setup Options

### Option 1: All-in-One Setup (Recommended)

This option sets up both the Crawl4AI server and the Remote API Client on the same machine.

1. **Clone this repository**:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME
   ```

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```

3. **Access the interface**:
   - Open your browser and go to `http://localhost:7860`

### Option 2: Client-Only Setup (Connect to Existing Server)

This option sets up only the Remote API Client to connect to an existing Crawl4AI server.

1. **Clone this repository**:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME
   ```

2. **Configure the environment**:
   ```bash
   cp .env.example .env
   ```

3. **Edit the .env file**:
   - Set `CRAWL4AI_API_URL` to your server's WebSocket URL
   - Example: `CRAWL4AI_API_URL=ws://your-server-ip:11235/mcp/ws`

4. **Build and run the client**:
   ```bash
   docker build -t crawl4ai-client .
   docker run -d --name crawl4ai-client -p 7860:7860 --env-file .env crawl4ai-client
   ```

5. **Access the interface**:
   - Open your browser and go to `http://localhost:7860`

## 🔧 Configuration Options

### Environment Variables

You can configure the following environment variables in the `.env` file:

- `CRAWL4AI_API_URL`: WebSocket URL of your Crawl4AI server
  - Example: `ws://your-server-ip:11235/mcp/ws`
  - Default: `ws://localhost:11235/mcp/ws`

- `MCP_SERVER_URL`: Alternative URL for the MCP server (if different from CRAWL4AI_API_URL)
  - Usually the same as `CRAWL4AI_API_URL`

- `OPENAI_API_KEY`: OpenAI API key for LLM-powered extraction (optional)
  - Only needed if you want to use OpenAI models for extraction

### Docker Compose Configuration

You can modify the `docker-compose.yml` file to customize the setup:

- **Memory limits**: Adjust the `memory` limits in the `deploy.resources` section
- **Ports**: Change the exposed ports if needed
- **Environment variables**: Add or modify environment variables

## 🔍 Verifying the Setup

### Check Container Status

```bash
docker-compose ps
```

You should see both `crawl4ai-server` and `crawl4ai-client` containers running.

### Check Logs

```bash
docker-compose logs -f
```

This will show the logs from both containers. Look for any error messages.

### Test the Connection

1. Open your browser and go to `http://localhost:7860`
2. Click the "Check Connection" button
3. You should see a success message with the available tools

## 🛠️ Troubleshooting

### Connection Issues

If you can't connect to the Crawl4AI server:

1. **Check if the server is running**:
   ```bash
   docker-compose ps crawl4ai-server
   ```

2. **Check server logs**:
   ```bash
   docker-compose logs crawl4ai-server
   ```

3. **Verify the WebSocket URL**:
   - Make sure the `CRAWL4AI_API_URL` is correct
   - If running on a different machine, make sure the IP/hostname is accessible

### Client Issues

If the client interface is not working:

1. **Check client logs**:
   ```bash
   docker-compose logs crawl4ai-client
   ```

2. **Restart the client**:
   ```bash
   docker-compose restart crawl4ai-client
   ```

3. **Rebuild the client**:
   ```bash
   docker-compose build crawl4ai-client
   docker-compose up -d crawl4ai-client
   ```

## 🔄 Updating

To update to the latest version:

1. **Pull the latest changes**:
   ```bash
   git pull
   ```

2. **Rebuild and restart the containers**:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

## 📚 Additional Resources

- **Crawl4AI Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
- **GitHub Repository**: [github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- **Docker Documentation**: [docs.docker.com](https://docs.docker.com)

## 🤝 Getting Help

If you encounter issues:

1. **Check the logs** as described in the Troubleshooting section
2. **Visit the GitHub repository** for known issues and solutions
3. **Join the community discussions** on GitHub

---

**Happy Crawling! 🚀🤖**