#!/usr/bin/env python3
"""
Crawl4AI Simple Gradio Interface for Hugging Face Spaces
A lightweight version that works reliably within HF Spaces constraints
"""

import gradio as gr
import asyncio
import json
import os
import sys
import traceback
from typing import Optional, Dict, Any
import tempfile
import base64
import requests
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

# Simple web scraping without heavy browser dependencies
import requests
from bs4 import BeautifulSoup
import html2text

class SimpleCrawler:
    """A simple crawler that works without browser automation"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        
    def crawl_url(self, url: str, css_selector: str = "", word_count_threshold: int = 10) -> Dict[str, Any]:
        """Crawl a URL and extract content"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # Make request
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Apply CSS selector if provided
            if css_selector.strip():
                try:
                    selected_elements = soup.select(css_selector)
                    if selected_elements:
                        # Create new soup with selected elements
                        new_soup = BeautifulSoup('<div></div>', 'html.parser')
                        for elem in selected_elements:
                            new_soup.div.append(elem)
                        soup = new_soup
                except Exception as e:
                    print(f"CSS selector error: {e}")
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else 'No title'
            
            # Convert to markdown
            html_content = str(soup)
            markdown_content = self.html_converter.handle(html_content)
            
            # Clean up markdown
            markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
            markdown_content = markdown_content.strip()
            
            # Filter by word count
            if word_count_threshold > 0:
                lines = markdown_content.split('\n')
                filtered_lines = []
                for line in lines:
                    words = line.strip().split()
                    if len(words) >= word_count_threshold or line.startswith('#') or line.startswith('*') or line.startswith('-'):
                        filtered_lines.append(line)
                markdown_content = '\n'.join(filtered_lines)
            
            # Extract links
            links = self._extract_links(soup, url)
            
            # Extract media
            media = self._extract_media(soup, url)
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            return {
                "success": True,
                "url": url,
                "title": title_text,
                "markdown": markdown_content,
                "cleaned_html": str(soup)[:5000],  # Limit size
                "links": links,
                "media": media,
                "metadata": metadata,
                "error_message": None,
                "word_count": len(markdown_content.split()),
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "url": url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Parsing failed: {str(e)}",
                "url": url,
                "traceback": traceback.format_exc()
            }
    
    def _extract_links(self, soup, base_url):
        """Extract internal and external links"""
        links = {"internal": [], "external": []}
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            link_domain = urlparse(full_url).netloc
            
            link_info = {
                "href": full_url,
                "text": text,
                "title": link.get('title', '')
            }
            
            if link_domain == base_domain:
                links["internal"].append(link_info)
            else:
                links["external"].append(link_info)
        
        return links
    
    def _extract_media(self, soup, base_url):
        """Extract media elements"""
        media = {"images": [], "videos": []}
        
        # Extract images
        for img in soup.find_all('img', src=True):
            src = urljoin(base_url, img['src'])
            media["images"].append({
                "src": src,
                "alt": img.get('alt', ''),
                "title": img.get('title', '')
            })
        
        # Extract videos
        for video in soup.find_all('video', src=True):
            src = urljoin(base_url, video['src'])
            media["videos"].append({
                "src": src,
                "title": video.get('title', '')
            })
        
        return media
    
    def _extract_metadata(self, soup):
        """Extract page metadata"""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # Headings
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    "level": i,
                    "text": heading.get_text().strip()
                })
        metadata["headings"] = headings
        
        return metadata

# Global crawler instance
crawler = SimpleCrawler()

def crawl_interface(url, css_selector, word_count, extract_links, extract_media):
    """Gradio interface function"""
    if not url.strip():
        return "Please enter a URL", "", "", "", ""
    
    try:
        result = crawler.crawl_url(url, css_selector, word_count)
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
**Timestamp:** {result.get('timestamp', 'N/A')}
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

# Create Gradio interface
def create_interface():
    with gr.Blocks(title="Crawl4AI - Simple Web Scraper", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🚀🤖 Crawl4AI: Simple Web Scraper
        
        Extract clean content from any webpage without complex browser automation!
        
        **Features:**
        - 📄 Convert web pages to clean markdown
        - 🔗 Extract and analyze links
        - 🖼️ Discover media elements
        - 🎯 CSS selector targeting
        - ⚡ Fast and lightweight
        - 🛡️ Works reliably in sandboxed environments
        """)
        
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
                
                crawl_btn = gr.Button("🚀 Scrape Website", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("""
                ### 💡 Tips:
                - **No browser required**: Uses simple HTTP requests
                - **CSS Selectors**: Target specific content areas
                - **Word Filter**: Remove short/empty lines
                - **Fast & Reliable**: Works in any environment
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
        
        # Examples
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
        
        This simplified version of Crawl4AI uses:
        - **HTTP Requests**: Direct web requests without browser automation
        - **BeautifulSoup**: HTML parsing and content extraction  
        - **html2text**: Clean markdown conversion
        - **CSS Selectors**: Precise content targeting
        
        ### 🚀 Full Crawl4AI Features
        
        For advanced features like JavaScript execution, screenshots, and AI-powered extraction:
        - **GitHub**: [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
        - **Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
        - **Python Package**: `pip install crawl4ai`
        
        **Built with ❤️ by the Crawl4AI community**
        """)
    
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