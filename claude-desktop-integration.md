# Claude Desktop Integration Example

This document shows how to integrate the Todo List Manager MCP Server with Claude Desktop.

## Configuration

### 1. Claude Desktop Configuration File

Add the following configuration to your Claude Desktop MCP settings file:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
              `~/.config/Claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "todo-manager": {
      "command": "python",
      "args": ["/path/to/MCPPoc/main.py"],
      "cwd": "/path/to/MCPPoc",
      "env": {
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "~/.todo-mcp-server.log"
      }
    }
  }
}
```

**Important**: The above configuration uses the default todo file location (`~/.todos.yaml`) with basic logging. See [Custom Configuration](#custom-todo-file-location) below for customization options.

### 2. Environment Setup

Ensure your Python environment has the required dependencies:

```bash
cd /path/to/MCPPoc
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage Examples

### Basic Todo Management

Once integrated with Claude Desktop, you can use natural language to manage todos:

#### Adding Todos
```
User: "Add a todo to buy groceries"
Claude: I'll add that todo for you.
[Uses add_todo tool with description "buy groceries"]
```

#### Listing Todos
```
User: "Show me my current todos"
Claude: Here are your current todos:
[Uses list_todos tool to fetch and display all todos]
```

#### Completing Todos
```
User: "Mark the grocery shopping todo as complete"
Claude: I'll mark that todo as completed.
[Uses list_todos to find the todo, then complete_todo with the ID]
```

#### Deleting Todos
```
User: "Delete the completed grocery todo"
Claude: I'll remove that completed todo for you.
[Uses list_todos to find completed todos, then delete_todo with the ID]
```

## Example Conversation Flow

```
User: I need help managing my daily tasks

Claude: I can help you manage your todos! I have access to a todo management system. What would you like to do?

User: Add a few tasks: "Call dentist", "Finish project report", and "Buy birthday gift"

Claude: I'll add those three tasks for you.

[Claude uses add_todo tool three times]

✅ Added: "Call dentist" (ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890)
✅ Added: "Finish project report" (ID: b2c3d4e5-f6g7-8901-bcde-f23456789012)
✅ Added: "Buy birthday gift" (ID: c3d4e5f6-g7h8-9012-cdef-345678901234)

All three tasks have been added to your todo list!

User: I just called the dentist. Mark that as done.

Claude: Great! I'll mark the "Call dentist" task as completed.

[Claude uses complete_todo tool with the dentist task ID]

✅ Completed: "Call dentist" - marked as done with timestamp 2025-01-15T14:30:22

User: What tasks do I still have pending?

Claude: Let me check your current pending tasks.

[Claude uses list_todos tool and filters for pending status]

You have 2 pending tasks:
1. "Finish project report" (Created: 2025-01-15T14:28:15)
2. "Buy birthday gift" (Created: 2025-01-15T14:28:16)

User: Actually, remove the birthday gift task - the party was cancelled

Claude: I'll remove the "Buy birthday gift" task from your list.

[Claude uses delete_todo tool with the birthday gift task ID]

✅ Deleted: "Buy birthday gift" has been removed from your todo list.

You now have 1 pending task remaining: "Finish project report"
```

## Todo File Location

### Default Location

By **default**, the MCP server stores todos in `~/.todos.yaml` (your home directory). This requires **no configuration** - the server will automatically create and manage this file.

### Custom Todo File Location

You may want to customize the todo file location for:
- **Organization**: Keep todos in Documents folder
- **Backup**: Store in cloud-synced directory  
- **Separation**: Different files for work/personal todos
- **Security**: Use encrypted filesystem location

Set a custom location by adding the `TODO_FILE` environment variable:

```json
{
  "mcpServers": {
    "todo-manager": {
      "command": "python",
      "args": ["/path/to/MCPPoc/main.py"],
      "cwd": "/path/to/MCPPoc",
      "env": {
        "TODO_FILE": "~/Documents/my-todos.yaml",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Multiple Todo Lists

You can run multiple instances for different contexts:

```json
{
  "mcpServers": {
    "work-todos": {
      "command": "python",
      "args": ["/path/to/MCPPoc/main.py"],
      "cwd": "/path/to/MCPPoc",
      "env": {
        "TODO_FILE": "~/.work_todos.yaml"
      }
    },
    "personal-todos": {
      "command": "python",
      "args": ["/path/to/MCPPoc/main.py"],
      "cwd": "/path/to/MCPPoc",
      "env": {
        "TODO_FILE": "~/.personal_todos.yaml"
      }
    }
  }
}
```

## Available MCP Tools

Claude Desktop will have access to these tools:

| Tool | Description | Parameters | Returns |
|------|-------------|------------|---------|
| `list_todos` | Get all todos | None | Array of todo objects |
| `add_todo` | Create new todo | `description` (string) | Created todo object |
| `complete_todo` | Mark todo as done | `id` (string) | Updated todo object |
| `delete_todo` | Remove todo | `id` (string) | Boolean success |
| `get_timestamp` | Get current time | None | ISO 8601 timestamp |

## Data Structure

Your todos are stored in YAML format:

```yaml
todos:
  - id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    description: "Call dentist"
    status: "done"
    created_at: "2025-01-15T14:28:15"
    completed_at: "2025-01-15T14:30:22"

  - id: "b2c3d4e5-f6g7-8901-bcde-f23456789012"
    description: "Finish project report"
    status: "pending"
    created_at: "2025-01-15T14:28:15"
    completed_at: null
```

## Troubleshooting

### Common Issues

1. **Server not starting**: Check Python path and dependencies
2. **Permission denied**: Ensure write access to todo file location
3. **Tool not found**: Verify MCP server configuration in Claude Desktop
4. **Empty responses**: Check server logs for error messages

### Debug Mode & Logging

The MCP server includes comprehensive logging to help debug issues and monitor Claude Desktop requests:

#### Logging Configuration

Configure logging through environment variables:

```json
{
  "mcpServers": {
    "todo-manager": {
      "command": "python",
      "args": ["/path/to/MCPPoc/main.py"],
      "cwd": "/path/to/MCPPoc",
      "env": {
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": "/tmp/todo-mcp-server.log"
      }
    }
  }
}
```

#### Available Log Levels

- **ERROR**: Only critical errors
- **WARNING**: Errors and warnings (failed operations)
- **INFO**: All MCP requests/responses + important events
- **DEBUG**: Detailed file operations and internal state

#### Log Output Examples

**INFO Level** (recommended for monitoring Claude Desktop requests):
```
2025-01-15T10:30:15 - todo-mcp-server - INFO - MCP Request: list_todos
2025-01-15T10:30:15 - todo-mcp-server - INFO - MCP Response: list_todos returned 3 todos
2025-01-15T10:30:22 - todo-mcp-server - INFO - MCP Request: add_todo(description='Buy groceries')
2025-01-15T10:30:22 - todo-mcp-server - INFO - MCP Response: add_todo created todo with ID a1b2c3d4-e5f6-7890-abcd-ef1234567890
2025-01-15T10:30:35 - todo-mcp-server - INFO - MCP Request: complete_todo(id='a1b2c3d4-e5f6-7890-abcd-ef1234567890')
2025-01-15T10:30:35 - todo-mcp-server - INFO - MCP Response: complete_todo marked 'Buy groceries' as done
```

**DEBUG Level** (detailed troubleshooting):
```
2025-01-15T10:30:15 - todo-mcp-server - DEBUG - Loading todos from /home/user/.todos.yaml
2025-01-15T10:30:15 - todo-mcp-server - DEBUG - Loaded 3 todos from file
2025-01-15T10:30:22 - todo-mcp-server - DEBUG - Saving 4 todos to /home/user/.todos.yaml
2025-01-15T10:30:22 - todo-mcp-server - DEBUG - Successfully saved 4 todos with secure permissions
```

#### Viewing Logs

**Console Output** (stderr):
```bash
# View logs in Claude Desktop's console/terminal if launched from terminal
# Or check system logs where Claude Desktop outputs are captured
```

**Log Files**:
```bash
# If LOG_FILE is specified
tail -f /tmp/todo-mcp-server.log

# Watch logs in real-time
tail -f /tmp/todo-mcp-server.log | grep "MCP Request"
```

#### Quick Logging Setup

For immediate debugging, create this configuration:

```json
{
  "mcpServers": {
    "todo-manager-debug": {
      "command": "python",
      "args": ["/path/to/MCPPoc/main.py"],
      "cwd": "/path/to/MCPPoc",
      "env": {
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "/tmp/claude-todo-debug.log"
      }
    }
  }
}
```

Then monitor in real-time:
```bash
tail -f /tmp/claude-todo-debug.log
```

#### What You'll See

When Claude Desktop makes requests to the MCP server, you'll see:

1. **Startup**: Server initialization and configuration
2. **MCP Requests**: Each tool call from Claude with parameters
3. **File Operations**: When todos are loaded/saved
4. **Responses**: Results returned to Claude Desktop
5. **Errors**: Failed operations (like completing non-existent todos)

### Testing the Integration

Test your setup by running the server manually:

```bash
cd /path/to/MCPPoc
python main.py
```

The server should start without errors and display MCP server information.

## Security Notes

- Todo files contain only task descriptions and timestamps
- No sensitive data should be stored in todo descriptions
- File permissions are set to user-only access (600)
- MCP server runs locally and doesn't transmit data externally
