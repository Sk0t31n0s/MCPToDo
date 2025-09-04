# MCP Todo List Manager

A Model Context Protocol (MCP) server that provides todo list management functionality with YAML-based persistence. This server integrates with Claude Desktop and other MCP clients to offer natural language todo management.

## Features

- **List todos**: View all todo items with their status and timestamps
- **Add todos**: Create new todo items with automatic timestamp tracking  
- **Complete todos**: Mark items as done with completion timestamps
- **Delete todos**: Remove todo items by ID
- **System timestamp**: Independent utility for fetching current time

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd MCPToDo
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   python main.py
   ```

3. **Test with Claude Desktop** (see [Integration Guide](claude-desktop-integration.md))

## Architecture

- **Single-file MCP server**: `main.py` contains the complete implementation
- **YAML persistence**: Human-readable storage in `~/.todos.yaml`
- **Atomic writes**: Safe file operations prevent data corruption
- **UUID identifiers**: Unique identifiers for each todo item
- **ISO 8601 timestamps**: Standard timestamp format for creation and completion

## Usage

### Running the Server

Start the MCP server:
```bash
python main.py
```

**With Logging** (to monitor Claude Desktop requests):
```bash
# Basic logging to console
LOG_LEVEL=INFO python main.py

# Debug logging with file output
LOG_LEVEL=DEBUG LOG_FILE=/tmp/todo-server.log python main.py
```

The server will start and expose the following MCP tools:

### Claude Desktop Integration

For detailed instructions on integrating with Claude Desktop, see [claude-desktop-integration.md](claude-desktop-integration.md).

**Quick Setup:**
1. Add server configuration to Claude Desktop MCP settings
2. Restart Claude Desktop 
3. Use natural language to manage todos through Claude

Example: *"Add a todo to buy groceries"* → Claude uses the MCP tools automatically

### Available Tools

1. **`list_todos`**
   - Lists all todo items
   - Returns: Array of todo objects

2. **`add_todo`**
   - Creates a new todo item
   - Parameters: `description` (string)
   - Returns: Created todo object with ID

3. **`complete_todo`**
   - Marks a todo as completed
   - Parameters: `id` (string)
   - Returns: Updated todo object or null if not found

4. **`delete_todo`**
   - Removes a todo item
   - Parameters: `id` (string)
   - Returns: Boolean success status

5. **`get_timestamp`**
   - Utility function for current system time
   - Returns: ISO 8601 formatted timestamp

### Data Storage

Todos are stored in `~/.todos.yaml` with the following structure:

```yaml
todos:
  - id: "uuid-string"
    description: "Todo description"
    status: "pending"  # or "done"
    created_at: "2025-01-01T12:00:00"
    completed_at: null  # or ISO timestamp when completed
```

#### File Permissions

The todo YAML file requires specific permissions for secure operation:

**Required Permissions for `~/.todos.yaml`:**
- **Owner**: Read + Write (rw-) - Required for loading and saving todos
- **Group**: No access (---) - Security best practice
- **Others**: No access (---) - Prevents unauthorized access

**Setting Correct Permissions:**
```bash
# Set restrictive permissions (600 = rw-------)
chmod 600 ~/.todos.yaml

# Verify permissions
ls -la ~/.todos.yaml
# Should show: -rw------- 1 username username
```

**Automatic Permission Setting:**
The application automatically sets secure permissions (600) when creating new todo files.

## Development

### Testing

The project includes comprehensive unit tests covering all core functionality:

Run the full test suite:
```bash
python -m pytest test_main.py -v
```

Run tests with coverage information:
```bash
pytest test_main.py
```

#### Test Coverage

**✅ All 21 tests pass successfully**

- **TestHelperFunctions** (6 tests): File operations, data loading/saving, timestamp generation, file permissions
- **TestMCPTools** (9 tests): CRUD operations for todos, error handling, edge cases
- **TestLogging** (4 tests): Logging configuration, log levels, file output, MCP request logging
- **TestIntegration** (2 tests): Complete workflows and data persistence

#### Test Categories

1. **File Operations**
   - Loading from non-existent files
   - Empty file handling 
   - Valid YAML data processing
   - Atomic file saving

2. **Todo Management**
   - Adding single and multiple todos
   - Completing existing and non-existent todos
   - Deleting todos with proper cleanup
   - Listing todos in various states

3. **Integration Workflows**
   - Complete todo lifecycle (create → complete → delete)
   - Data persistence across server restarts
   - Concurrent operations safety

### Code Quality

Check code style:
```bash
flake8 main.py
```

**Current Status**: ✅ All 21 tests pass. Minor style warnings present (line length, whitespace)

### Development Setup

1. Install development dependencies from `requirements.txt`
2. Use virtual environment for isolation
3. Follow PEP 8 style guidelines
4. Run tests before committing changes

## Security & Permissions

### File System Permissions

#### Todo Data File (`~/.todos.yaml`)
- **Required**: `600` (rw-------) - Owner read/write only
- **Purpose**: Protects personal todo data from other users
- **Auto-set**: Application creates file with secure permissions

#### Application Directory
- **Python files**: `644` (rw-r--r--) - Standard read permissions
- **Virtual environment**: `755` (rwxr-xr-x) - Standard directory permissions
- **Temporary files**: `600` (rw-------) - Used during atomic writes

#### Home Directory Considerations
- **Parent directory**: Must have execute permission for user (`x` bit)
- **Example**: If using `~/Documents/todos.yaml`, ensure `~/Documents/` is accessible
- **Verification**: `ls -ld ~/` should show execute permission

### Security Best Practices

#### 1. File Location Security
```bash
# ✅ Good: User home directory
~/.todos.yaml
~/Documents/my-todos.yaml

# ❌ Avoid: Shared or system directories
/tmp/todos.yaml          # Accessible by all users
/var/shared/todos.yaml   # May have broad permissions
```

#### 2. Directory Permissions
```bash
# Verify home directory access
ls -ld ~/
# Should show: drwx------ or drwxr-xr-x (user must have 'x')

# Check custom directory permissions
mkdir -p ~/my-todos/
chmod 700 ~/my-todos/    # Restrictive directory access
```

#### 3. Process Permissions
- **User Context**: MCP server runs as current user
- **No Root Required**: Application doesn't need elevated privileges
- **Isolation**: Each user's todos are isolated by file system permissions

#### 4. Network Security
- **Local Only**: MCP server binds to local process communication
- **No Network Ports**: Doesn't open TCP/UDP ports
- **Process Communication**: Uses stdin/stdout for MCP protocol

### Common Permission Issues

#### Issue: "Permission Denied" when accessing todo file
```bash
# Diagnosis
ls -la ~/.todos.yaml

# Solutions
chmod 600 ~/.todos.yaml              # Fix file permissions
chown $USER:$USER ~/.todos.yaml      # Fix ownership if needed
```

#### Issue: Cannot create todo file in directory
```bash
# Diagnosis
ls -ld ~/target/directory/

# Solutions
chmod 755 ~/target/directory/        # Ensure directory is writable
mkdir -p ~/target/directory/         # Create directory if missing
```

#### Issue: Application cannot access home directory
```bash
# Diagnosis
ls -ld ~/

# Solution
chmod u+x ~/                         # Ensure execute permission on home
```

### Multi-User Considerations

#### Separate User Data
- Each user gets their own todo file: `~/.todos.yaml`
- No shared state between users
- File system provides natural isolation

#### System Administrator Setup
```bash
# For multiple users on shared system
for user in alice bob charlie; do
    sudo -u $user touch /home/$user/.todos.yaml
    sudo chmod 600 /home/$user/.todos.yaml
    sudo chown $user:$user /home/$user/.todos.yaml
done
```

#### Container/Docker Permissions
```dockerfile
# Ensure proper user context
RUN adduser --disabled-password --gecos '' todouser
USER todouser
WORKDIR /home/todouser
# Application will create .todos.yaml with correct permissions
```

### Security Limitations

⚠️ **Current Security Gaps** (See TODO.md for improvements):
- No input validation on todo descriptions
- No file size limits (potential DoS)
- No encryption at rest
- Uses `yaml.load()` instead of `yaml.safe_load()` (code execution risk)

### Recommended Setup Checklist

- [ ] Verify home directory has execute permission (`ls -ld ~/`)
- [ ] Use default location `~/.todos.yaml` or secure custom path
- [ ] Avoid shared directories like `/tmp/` or `/var/shared/`
- [ ] Run application as regular user (not root)
- [ ] Check file permissions after first run (`ls -la ~/.todos.yaml`)
- [ ] Consider separate todo files for different contexts (work/personal)

## Configuration

Currently uses hardcoded configuration:
- **Storage Location**: `~/.todos.yaml`
- **Timestamp Format**: ISO 8601 with second precision

## Dependencies

- **mcp**: MCP server framework (≥0.2.0)
- **ruamel.yaml**: YAML processing with formatting preservation (≥0.18.6)
- **pytest**: Testing framework (≥8.3.0)
- **flake8**: Code style checker (≥7.1.0)

## License

[Add license information]

## Contributing

[Add contribution guidelines]