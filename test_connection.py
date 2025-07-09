#!/usr/bin/env python3
"""
Test script to verify connection to a Crawl4AI server
"""

import asyncio
import json
import os
import sys
import uuid
import websockets
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Define JSON-RPC request model
class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: Dict[str, Any]

# Get the server URL from environment variables
CRAWL4AI_API_URL = os.getenv("CRAWL4AI_API_URL", "ws://localhost:11235/mcp/ws")

async def test_connection():
    """Test connection to the Crawl4AI server"""
    print(f"Connecting to {CRAWL4AI_API_URL}...")
    
    try:
        # Connect to the WebSocket server
        async with websockets.connect(CRAWL4AI_API_URL) as websocket:
            # Initialize the connection
            init_id = str(uuid.uuid4())
            init_request = JsonRpcRequest(
                id=init_id,
                method="initialize",
                params={
                    "client_info": {
                        "name": "Crawl4AI Test Client",
                        "version": "1.0.0"
                    }
                }
            )
            
            await websocket.send(init_request.model_dump_json())
            response = await websocket.recv()
            print("✅ Connection initialized!")
            
            # List available tools
            tools_id = str(uuid.uuid4())
            tools_request = JsonRpcRequest(
                id=tools_id,
                method="workspace/listTools",
                params={}
            )
            
            await websocket.send(tools_request.model_dump_json())
            tools_response = json.loads(await websocket.recv())
            
            if "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                tool_names = [t.get("name") for t in tools]
                
                print(f"✅ Connected successfully!")
                print(f"Available tools: {', '.join(tool_names)}")
                
                # Test a simple tool call if 'md' is available
                if 'md' in tool_names:
                    print("\nTesting 'md' tool with example.com...")
                    
                    md_id = str(uuid.uuid4())
                    md_request = JsonRpcRequest(
                        id=md_id,
                        method="workspace/callTool",
                        params={
                            "name": "md",
                            "arguments": {
                                "url": "https://example.com",
                                "f": "fit",
                                "q": None,
                                "c": "0",
                            }
                        }
                    )
                    
                    await websocket.send(md_request.model_dump_json())
                    md_response = json.loads(await websocket.recv())
                    
                    if "result" in md_response:
                        content = md_response["result"].get("content", [])
                        if content and len(content) > 0:
                            result = json.loads(content[0].get("text", "{}"))
                            if result.get("success", False):
                                print("✅ Tool call successful!")
                                print(f"Title: {result.get('title', 'N/A')}")
                                print(f"Word count: {result.get('word_count', 0)}")
                                print(f"Markdown preview: {result.get('markdown', '')[:100]}...")
                            else:
                                print(f"❌ Tool call failed: {result.get('error', 'Unknown error')}")
                        else:
                            print("❌ No content in response")
                    else:
                        print(f"❌ Tool call failed: {md_response.get('error', 'Unknown error')}")
                
                return True
            else:
                print(f"❌ Failed to list tools: {tools_response.get('error', 'Unknown error')}")
                return False
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