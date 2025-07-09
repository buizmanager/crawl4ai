#!/usr/bin/env python3
"""
Test script to verify connection to a Crawl4AI server
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import MCP client
try:
    from mcp.client.websocket import websocket_client
    from mcp.client.session import ClientSession
except ImportError:
    print("Error: mcp-sdk not installed. Please install it with:")
    print("pip install mcp-sdk[ws]")
    sys.exit(1)

# Get the server URL from environment variables
CRAWL4AI_API_URL = os.getenv("CRAWL4AI_API_URL", "ws://localhost:11235/mcp/ws")

async def test_connection():
    """Test connection to the Crawl4AI server"""
    print(f"Connecting to {CRAWL4AI_API_URL}...")
    
    try:
        # Connect to the MCP server
        async with websocket_client(CRAWL4AI_API_URL) as (reader, writer):
            # Create a client session
            async with ClientSession(reader, writer) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                tools_response = await session.list_tools()
                tool_names = [t.name for t in tools_response.tools]
                
                print(f"✅ Connected successfully!")
                print(f"Available tools: {', '.join(tool_names)}")
                
                # Test a simple tool call if 'md' is available
                if 'md' in tool_names:
                    print("\nTesting 'md' tool with example.com...")
                    response = await session.call_tool(
                        "md",
                        {
                            "url": "https://example.com",
                            "f": "fit",
                            "q": None,
                            "c": "0",
                        },
                    )
                    
                    # Parse the response
                    result = json.loads(response.content[0].text)
                    if result.get("success", False):
                        print("✅ Tool call successful!")
                        print(f"Title: {result.get('title', 'N/A')}")
                        print(f"Word count: {result.get('word_count', 0)}")
                        print(f"Markdown preview: {result.get('markdown', '')[:100]}...")
                    else:
                        print(f"❌ Tool call failed: {result.get('error', 'Unknown error')}")
                
                return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the async function
    if asyncio.run(test_connection()):
        print("\n🎉 All tests passed! The Crawl4AI server is accessible.")
    else:
        print("\n❌ Tests failed. Please check your server configuration.")
        sys.exit(1)