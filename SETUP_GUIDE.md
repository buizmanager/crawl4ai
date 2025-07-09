# 🚀 Crawl4AI Remote API Client Setup Guide

This guide will help you set up the Crawl4AI Remote API Client to connect to a remote Crawl4AI server.

## 📋 Prerequisites

### For Docker Installation

1. **Docker**: Install Docker on your server
   - [Docker Installation Guide](https://docs.docker.com/get-docker/)

2. **Docker Compose**: Install Docker Compose
   - [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)

3. **Server with sufficient resources**:
   - At least 4GB RAM
   - At least 10GB free disk space
   - Internet connectivity

### For Hugging Face Spaces Installation

1. **Hugging Face Account**: Create an account on [huggingface.co](https://huggingface.co)
2. **Remote Crawl4AI Server**: Access to a running Crawl4AI server with WebSocket endpoint
3. **Basic Git Knowledge**: For cloning and pushing to repositories

## 🎯 Setup Options

### Option 1: Hugging Face Spaces Setup (Recommended)

This option deploys the Remote API Client on Hugging Face Spaces, which provides a free, hosted environment.

1. **Create a new Space**:
   - Go to [huggingface.co/new-space](https://huggingface.co/new-space)
   - Fill in the details:
     - **Owner**: Your username or organization
     - **Space name**: Choose a name (e.g., "crawl4ai-remote-client")
     - **License**: Apache 2.0
     - **SDK**: Select "Gradio" from the dropdown
     - **Space hardware**: Start with "CPU basic" (free tier)
     - **Visibility**: Choose "Public" or "Private" based on your needs
   - Click "Create Space"

2. **Upload files to your Space**:
   - Option A: Using the web interface
     - In your Space, click on the "Files" tab
     - Upload all the files from this repository
   - Option B: Using Git (Recommended)
     ```bash
     git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
     cd YOUR_SPACE_NAME
     git clone -b huggingface_spaces_Crawl4AI-API-ENDPOINT https://github.com/buizmanager/crawl4ai.git temp
     cp -r temp/* .
     cp temp/.gitignore .
     cp temp/.env.example .env
     rm -rf temp
     git add .
     git commit -m "Add Crawl4AI Remote API Client"
     git push
     ```

3. **Configure environment variables**:
   - Go to your Space settings (click the ⚙️ icon)
   - Scroll down to the "Repository secrets" section
   - Add the following environment variable:
     - **Name**: `CRAWL4AI_API_URL`
     - **Value**: The WebSocket URL of your Crawl4AI server (e.g., `ws://your-server-ip:11235/mcp/ws`)
   - Click "Add secret"

4. **Access the interface**:
   - Go to the "App" tab of your Space
   - Wait for the build to complete
   - Use the interface to interact with your Crawl4AI server

### Option 2: Docker All-in-One Setup

This option sets up both the Crawl4AI server and the Remote API Client on the same machine.

1. **Clone this repository**:
   ```bash
   git clone https://github.com/buizmanager/crawl4ai.git -b huggingface_spaces_Crawl4AI-API-ENDPOINT
   cd crawl4ai
   ```

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```

3. **Access the interface**:
   - Open your browser and go to `http://localhost:7860`

### Option 3: Docker Client-Only Setup (Connect to Existing Server)

This option sets up only the Remote API Client to connect to an existing Crawl4AI server.

1. **Clone this repository**:
   ```bash
   git clone https://github.com/buizmanager/crawl4ai.git -b huggingface_spaces_Crawl4AI-API-ENDPOINT
   cd crawl4ai
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

### Hugging Face Spaces Issues

If you're having issues with your Hugging Face Space:

1. **Check build logs**:
   - Go to the "Settings" tab of your Space
   - Click on "Build logs" to see what went wrong during the build process

2. **Check runtime logs**:
   - Go to the "Logs" tab of your Space
   - Look for error messages that might indicate what's wrong

3. **Common issues and solutions**:
   - **WebSocket connection errors**: Make sure your Crawl4AI server is accessible from the internet
   - **CORS issues**: Your Crawl4AI server might need to allow requests from your Space's domain
   - **Build failures**: Check if all dependencies are correctly specified in requirements.txt
   - **Timeout errors**: Consider upgrading your Space's hardware if operations take too long

4. **Restart your Space**:
   - Go to the "Settings" tab
   - Click on "Factory reboot" to restart your Space

### Docker Connection Issues

If you can't connect to the Crawl4AI server when using Docker:

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

### Docker Client Issues

If the client interface is not working when using Docker:

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

### Updating Hugging Face Spaces

To update your Hugging Face Space to the latest version:

1. **Using the web interface**:
   - Go to the "Files" tab of your Space
   - Click on each file you want to update
   - Click "Edit" and paste the new content
   - Click "Save"

2. **Using Git**:
   ```bash
   # Clone your Space repository
   git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   cd YOUR_SPACE_NAME
   
   # Pull the latest changes from the original repository
   git remote add upstream https://github.com/buizmanager/crawl4ai.git
   git fetch upstream huggingface_spaces_Crawl4AI-API-ENDPOINT
   git merge upstream/huggingface_spaces_Crawl4AI-API-ENDPOINT
   
   # Push the changes to your Space
   git push
   ```

### Updating Docker Installation

To update your Docker installation to the latest version:

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
- **Hugging Face Spaces Documentation**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Gradio Documentation**: [gradio.app/docs](https://gradio.app/docs/)

## 🤝 Getting Help

If you encounter issues:

1. **Check the logs** as described in the Troubleshooting section
2. **Visit the GitHub repository** for known issues and solutions
3. **Join the community discussions** on GitHub

---

**Happy Crawling! 🚀🤖**