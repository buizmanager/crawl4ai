# 🚀 Deploying Crawl4AI to Hugging Face Spaces

This guide will help you deploy Crawl4AI to Hugging Face Spaces successfully.

## 📋 Prerequisites

1. **Hugging Face Account**: Sign up at [huggingface.co](https://huggingface.co)
2. **Git**: Installed on your local machine
3. **Basic knowledge**: Familiarity with Git and Hugging Face Spaces

## 🎯 Two Deployment Options

### Option 1: Simple Version (Recommended for HF Spaces)

**Files needed:**
- `app_simple.py` → rename to `app.py`
- `requirements_simple.txt` → rename to `requirements.txt`
- `README_HF.md` → rename to `README.md`

**Advantages:**
- ✅ No browser dependencies
- ✅ Fast startup time
- ✅ Reliable in sandboxed environments
- ✅ Lower memory usage
- ✅ Works with HF Spaces constraints

**Limitations:**
- ❌ No JavaScript execution
- ❌ No screenshots/PDFs
- ❌ No complex browser automation

### Option 2: Full Version (Advanced)

**Files needed:**
- `app.py` (full version)
- `requirements_hf.txt` → rename to `requirements.txt`
- `README_HF.md` → rename to `README.md`
- `Dockerfile.hf` → rename to `Dockerfile`

**Advantages:**
- ✅ Full Crawl4AI features
- ✅ JavaScript execution
- ✅ Screenshots and PDFs
- ✅ Browser automation

**Challenges:**
- ⚠️ Higher memory usage
- ⚠️ Longer startup time
- ⚠️ May hit HF Spaces limits
- ⚠️ Browser setup complexity

## 🚀 Step-by-Step Deployment (Simple Version)

### Step 1: Create a New Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Choose a name for your space (e.g., `crawl4ai-scraper`)
3. Select **Gradio** as the SDK
4. Choose **Public** or **Private** visibility
5. Click **Create Space**

### Step 2: Clone Your Space Repository

```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME
```

### Step 3: Copy Files

Copy these files to your space directory:

```bash
# Copy and rename the simple version files
cp /path/to/crawl4ai/app_simple.py ./app.py
cp /path/to/crawl4ai/requirements_simple.txt ./requirements.txt
cp /path/to/crawl4ai/README_HF.md ./README.md
```

### Step 4: Create Space Configuration

Create a file called `README.md` with the following header:

```yaml
---
title: Crawl4AI Web Scraper
emoji: 🚀🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Simple web scraper and content extractor
---
```

### Step 5: Deploy

```bash
git add .
git commit -m "Initial deployment of Crawl4AI simple scraper"
git push
```

### Step 6: Monitor Deployment

1. Go to your space URL: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`
2. Check the **Logs** tab for any errors
3. Wait for the build to complete (usually 2-5 minutes)

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. **Build Timeout**
```
Error: Build timeout after 1800 seconds
```
**Solution**: Use the simple version instead of the full version.

#### 2. **Memory Issues**
```
Error: Container killed due to memory limit
```
**Solutions**:
- Use `app_simple.py` instead of `app.py`
- Reduce concurrent processing
- Add memory optimization flags

#### 3. **Permission Errors**
```
Error: Permission denied
```
**Solution**: Ensure all files have proper permissions and use the simple version.

#### 4. **Import Errors**
```
ModuleNotFoundError: No module named 'crawl4ai'
```
**Solution**: Check that `requirements.txt` includes all necessary dependencies.

### Debug Steps

1. **Check Logs**: Always check the build and runtime logs in HF Spaces
2. **Test Locally**: Run the app locally first:
   ```bash
   python app.py
   ```
3. **Simplify**: Start with the simple version and add features gradually
4. **Memory Check**: Monitor memory usage in the logs

## 🎛️ Configuration Options

### Environment Variables

You can set these in your Space settings:

- `OPENAI_API_KEY`: For LLM-powered extraction (optional)
- `GRADIO_SERVER_NAME`: Set to `0.0.0.0`
- `GRADIO_SERVER_PORT`: Set to `7860`

### Space Settings

In your Space settings, you can:
- **Upgrade to GPU**: For better performance (paid feature)
- **Set secrets**: For API keys and sensitive data
- **Configure domains**: For custom domains

## 📊 Performance Optimization

### For Simple Version:
- Uses minimal dependencies
- Fast HTTP requests
- Efficient HTML parsing
- Low memory footprint

### For Full Version:
- Enable browser pooling
- Use headless mode
- Optimize browser flags
- Implement caching

## 🔄 Updates and Maintenance

### Updating Your Space:

```bash
# Pull latest changes
git pull

# Make your updates
# ... edit files ...

# Deploy updates
git add .
git commit -m "Update: description of changes"
git push
```

### Monitoring:
- Check logs regularly
- Monitor memory usage
- Test functionality after updates
- Keep dependencies updated

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs** in your HF Space
2. **Try the simple version** first
3. **Search existing issues** in the Crawl4AI GitHub repo
4. **Create an issue** with detailed error logs
5. **Join the community** discussions

## 📚 Additional Resources

- **Crawl4AI Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
- **Hugging Face Spaces Docs**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Gradio Documentation**: [gradio.app/docs](https://gradio.app/docs)
- **GitHub Repository**: [github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)

---

**Happy Scraping! 🚀🤖**