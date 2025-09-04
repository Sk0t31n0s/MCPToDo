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

# Default location for storing todos (customizable via TODO_FILE environment variable)
TODO_FILE = Path(os.getenv("TODO_FILE", str(Path.home() / ".todos.yaml"))).expanduser()

# Initialize YAML parser/writer
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.default_flow_style = False

# Configure logging
logger = logging.getLogger("todo-mcp-server")


def setup_logging():
    """Setup logging configuration with default debug logging and file output."""
    # Default to DEBUG level for better troubleshooting
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s")
    
    # Configure the logger
    logger.setLevel(getattr(logging, log_level, logging.DEBUG))
    
    # Create console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)
    
    # Default log file location
    default_log_file = Path.home() / ".todo-mcp-server.log"
    log_file = os.getenv("LOG_FILE", str(default_log_file))
    
    if log_file:
        try:
            # Ensure log file directory exists
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to setup file logging to {log_file}: {e}")
    
    logger.info(f"Logging configured: level={log_level}, file={log_file}")
    logger.debug(f"Todo file location: {TODO_FILE}")
    logger.debug(f"Todo file exists: {TODO_FILE.exists()}")

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
    logger.debug(f"Data to save: {data}")
    
    # Ensure parent directory exists
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Parent directory {TODO_FILE.parent} exists: {TODO_FILE.parent.exists()}")
    
    # Create temp file in same directory to avoid cross-device issues
    tmp_fd, tmp_path = tempfile.mkstemp(dir=TODO_FILE.parent)
    logger.debug(f"Created temp file: {tmp_path}")
    
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
            logger.debug("Writing data to temp file")
            yaml.dump(data, tmp_file)
            tmp_file.flush()  # Ensure data is written
            os.fsync(tmp_file.fileno())  # Force write to disk
        
        logger.debug(f"Temp file size: {os.path.getsize(tmp_path)} bytes")
        logger.debug(f"Replacing {TODO_FILE} with {tmp_path}")
        os.replace(tmp_path, TODO_FILE)  # atomic rename
        
        # Set secure file permissions (600 = rw-------)
        os.chmod(TODO_FILE, 0o600)
        final_size = os.path.getsize(TODO_FILE)
        logger.debug(f"Successfully saved {todo_count} todos with secure permissions")
        logger.debug(f"Final file size: {final_size} bytes")
        logger.info(f"Todo file saved successfully: {TODO_FILE} ({final_size} bytes)")
        
    except Exception as e:
        logger.error(f"Failed to save todos: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # cleanup temp file on error
        try:
            os.unlink(tmp_path)
            logger.debug(f"Cleaned up temp file: {tmp_path}")
        except Exception as cleanup_e:
            logger.debug(f"Failed to cleanup temp file {tmp_path}: {cleanup_e}")
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
    logger.debug("Loading existing todos")
    data = load_todos()
    logger.debug(f"Current todos count before adding: {len(data['todos'])}")
    
    new_item = {
        "id": str(uuid.uuid4()),  # unique identifier
        "description": description,
        "status": "pending",
        "created_at": current_timestamp(),
        "completed_at": None
    }
    logger.debug(f"Created new todo item: {new_item}")
    
    data["todos"].append(new_item)
    logger.debug(f"Todos count after adding: {len(data['todos'])}")
    logger.debug("About to save todos to file")
    
    save_todos(data)
    logger.info(f"MCP Response: add_todo created todo with ID {new_item['id']}")
    
    # Verify the save worked by reloading
    verification_data = load_todos()
    logger.debug(f"Verification: reloaded {len(verification_data['todos'])} todos from file")
    
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
    logger.debug(f"MCP tool call received: {name} with arguments: {arguments}")
    
    if name == "list_todos":
        result = list_todos()
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "add_todo":
        description = arguments.get("description")
        if not description:
            logger.warning("add_todo called without description parameter")
            return [TextContent(type="text", text="Error: description parameter is required")]
        logger.debug(f"Calling add_todo with description: '{description}'")
        result = add_todo(description)
        logger.debug(f"add_todo returned: {result}")
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
