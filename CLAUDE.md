# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server proof-of-concept that provides todo list management functionality. The server stores todos in a YAML file (`~/.todos.yaml` by default) and exposes tools for creating, listing, updating, and deleting todo items.

## Architecture

- **main.py**: Single-file MCP server implementation using the `mcp` framework
- **Data Storage**: YAML file-based persistence with atomic writes for data safety
- **Todo Structure**: Each todo has id, description, status (pending/done), created_at, and completed_at timestamps

## Development Commands

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Running the Server
```bash
python main.py
```

### Testing
```bash
pytest
```

### Code Quality
```bash
flake8 main.py
```

## Key Implementation Details

- Uses `ruamel.yaml` for YAML handling with proper formatting preservation
- Implements atomic file writes using temp files to prevent data corruption
- Todo IDs are UUIDs for uniqueness
- Timestamps are ISO 8601 format with second precision
- Default todo storage location: `~/.todos.yaml`

## MCP Tools Exposed

1. `list_todos`: Retrieve all todo items
2. `add_todo`: Create new todo with description
3. `complete_todo`: Mark todo as done by ID
4. `delete_todo`: Remove todo by ID
5. `get_timestamp`: Utility for current system timestamp

## Integration

- **claude-desktop-integration.md**: Complete guide for Claude Desktop integration
- **test_main.py**: Comprehensive test suite with 16 tests (all passing)
- Natural language interface through Claude Desktop MCP integration