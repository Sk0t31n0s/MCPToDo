"""
Todo List Manager MCP Server
----------------------------
Proof-of-concept MCP server that manages a simple todo list stored
in a YAML file on the local system.

Features:
- List todos
- Add todo with timestamp
- Mark todo as complete (with timestamp)
- Delete todo
- Fetch current system timestamp (independent utility)

Requirements:
    pip install mcp ruamel.yaml
"""

import os
import uuid
import tempfile
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
import json
from ruamel.yaml import YAML

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

# Default location for storing todos (can be customized later)
TODO_FILE = Path.home() / ".todos.yaml"

# Initialize YAML parser/writer
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.default_flow_style = False

# Configure logging
logger = logging.getLogger("todo-mcp-server")


def setup_logging():
    """Setup logging configuration based on environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Configure the logger
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)
    
    # Also log to file if specified
    log_file = os.getenv("LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    logger.info(f"Logging configured: level={log_level}, file={log_file or 'None'}")

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------

def load_todos() -> dict:
    """Load todos from YAML file. Returns dict structure.
    If file does not exist, initialize with empty todos list."""
    logger.debug(f"Loading todos from {TODO_FILE}")
    
    if not TODO_FILE.exists():
        logger.debug("Todo file doesn't exist, returning empty list")
        return {"todos": []}

    with open(TODO_FILE, "r", encoding="utf-8") as f:
        data = yaml.load(f)
        if data is None:
            logger.debug("Todo file is empty, returning empty list")
            return {"todos": []}
        
        todo_count = len(data.get("todos", []))
        logger.debug(f"Loaded {todo_count} todos from file")
        return data


def save_todos(data: dict) -> None:
    """Safely save todos to YAML using atomic write to prevent corruption."""
    todo_count = len(data.get("todos", []))
    logger.debug(f"Saving {todo_count} todos to {TODO_FILE}")
    
    # Create temp file in same directory to avoid cross-device issues
    tmp_fd, tmp_path = tempfile.mkstemp(dir=TODO_FILE.parent)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
            yaml.dump(data, tmp_file)
        os.replace(tmp_path, TODO_FILE)  # atomic rename
        # Set secure file permissions (600 = rw-------)
        os.chmod(TODO_FILE, 0o600)
        logger.debug(f"Successfully saved {todo_count} todos with secure permissions")
    except Exception as e:
        logger.error(f"Failed to save todos: {e}")
        # cleanup temp file on error
        try:
            os.unlink(tmp_path)
        except:
            pass  # temp file might already be cleaned up
        raise


def current_timestamp() -> str:
    """Return system timestamp in ISO 8601 format."""
    return datetime.now().isoformat(timespec="seconds")


# ----------------------------------------------------------------------
# MCP Server Setup
# ----------------------------------------------------------------------

server = Server("todo-list-manager")


def list_todos() -> List[dict]:
    """Return all todos as JSON-serializable list of dicts."""
    logger.info("MCP Request: list_todos")
    data = load_todos()
    todo_count = len(data["todos"])
    logger.info(f"MCP Response: list_todos returned {todo_count} todos")
    return data["todos"]


def add_todo(description: str) -> dict:
    """Add a new todo item with ID, pending status, and created timestamp."""
    logger.info(f"MCP Request: add_todo(description='{description}')")
    data = load_todos()
    new_item = {
        "id": str(uuid.uuid4()),  # unique identifier
        "description": description,
        "status": "pending",
        "created_at": current_timestamp(),
        "completed_at": None
    }
    data["todos"].append(new_item)
    save_todos(data)
    logger.info(f"MCP Response: add_todo created todo with ID {new_item['id']}")
    return new_item


def complete_todo(id: str) -> Optional[dict]:
    """Mark a todo as completed if found. Returns updated item or None."""
    logger.info(f"MCP Request: complete_todo(id='{id}')")
    data = load_todos()
    for item in data["todos"]:
        if item["id"] == id:
            item["status"] = "done"
            item["completed_at"] = current_timestamp()
            save_todos(data)
            logger.info(f"MCP Response: complete_todo marked '{item['description']}' as done")
            return item
    logger.warning(f"MCP Response: complete_todo failed - todo with ID '{id}' not found")
    return None


def delete_todo(id: str) -> bool:
    """Delete a todo by ID. Returns True if deleted, False otherwise."""
    logger.info(f"MCP Request: delete_todo(id='{id}')")
    data = load_todos()
    before_count = len(data["todos"])
    
    # Find the todo being deleted for logging
    deleted_todo = next((t for t in data["todos"] if t["id"] == id), None)
    
    data["todos"] = [t for t in data["todos"] if t["id"] != id]
    after_count = len(data["todos"])
    if after_count < before_count:
        save_todos(data)
        desc = deleted_todo['description'] if deleted_todo else "unknown"
        logger.info(f"MCP Response: delete_todo deleted '{desc}' (ID: {id})")
        return True
    logger.warning(f"MCP Response: delete_todo failed - todo with ID '{id}' not found")
    return False


def get_timestamp() -> str:
    """Independent utility to fetch current timestamp."""
    logger.info("MCP Request: get_timestamp")
    timestamp = current_timestamp()
    logger.info(f"MCP Response: get_timestamp returned {timestamp}")
    return timestamp


@server.list_tools()
async def handle_list_tools():
    """List available tools"""
    return [
        Tool(
            name="list_todos",
            description="List all todo items stored in the YAML file",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="add_todo",
            description="Add a new todo item with system timestamp",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Todo description"}
                },
                "required": ["description"]
            }
        ),
        Tool(
            name="complete_todo",
            description="Mark a todo as completed by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Todo item ID"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="delete_todo",
            description="Delete a todo item by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Todo item ID"}
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_timestamp",
            description="Fetch current system timestamp in ISO 8601 format",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    if name == "list_todos":
        result = list_todos()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "add_todo":
        description = arguments.get("description")
        if not description:
            return [TextContent(type="text", text="Error: description parameter is required")]
        result = add_todo(description)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "complete_todo":
        todo_id = arguments.get("id")
        if not todo_id:
            return [TextContent(type="text", text="Error: id parameter is required")]
        result = complete_todo(todo_id)
        if result:
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        else:
            return [TextContent(type="text", text=f"Error: Todo with ID '{todo_id}' not found")]
    
    elif name == "delete_todo":
        todo_id = arguments.get("id")
        if not todo_id:
            return [TextContent(type="text", text="Error: id parameter is required")]
        result = delete_todo(todo_id)
        if result:
            return [TextContent(type="text", text=f"Todo with ID '{todo_id}' deleted successfully")]
        else:
            return [TextContent(type="text", text=f"Error: Todo with ID '{todo_id}' not found")]
    
    elif name == "get_timestamp":
        result = get_timestamp()
        return [TextContent(type="text", text=result)]
    
    else:
        return [TextContent(type="text", text=f"Error: Unknown tool '{name}'")]


# ----------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------

async def main():
    # Setup logging first
    setup_logging()
    logger.info("Todo List Manager MCP Server starting...")
    
    # Import stdio server utilities
    from mcp.server.stdio import stdio_server
    
    # Run the MCP server with STDIO transport
    logger.info("MCP server initialized, starting server...")
    async with stdio_server() as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
