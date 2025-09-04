# TODO: Security and Functionality Improvements

## Critical Security Fixes

### High Priority
- [ ] **Fix YAML Deserialization Vulnerability**
  - Replace `yaml.load()` with `yaml.safe_load()` in `load_todos()` function
  - Prevents arbitrary code execution from malicious YAML files
  - Location: `main.py:52`

- [ ] **Add Input Validation**
  - Sanitize todo descriptions to prevent injection attacks
  - Validate UUID format in tool parameters
  - Limit description length to prevent DoS via large payloads

- [ ] **Secure File Permissions**
  - Set restrictive permissions (600) on todo YAML file
  - Only owner should have read/write access
  - Location: `save_todos()` function

### Medium Priority
- [ ] **Path Validation**
  - Validate TODO_FILE path to prevent directory traversal
  - Consider making file path configurable through environment variable
  - Add path sanitization

- [ ] **Error Handling Improvements**
  - Sanitize error messages to avoid path disclosure
  - Add structured error responses instead of stack traces
  - Log security events appropriately

## Functionality Enhancements

### Core Features
- [ ] **Search and Filtering**
  - Add `search_todos` tool with text search capability
  - Filter by status (pending, done, all)
  - Search by date ranges

- [ ] **Todo Categories/Tags**
  - Add optional tags field to todo structure
  - Implement `add_tag` and `remove_tag` tools
  - Filter todos by tags

- [ ] **Priority System**
  - Add priority field (low, medium, high, urgent)
  - Sort todos by priority
  - Update data structure in YAML

- [ ] **Due Dates**
  - Add optional `due_date` field
  - Implement `set_due_date` tool
  - Add overdue todo identification

### Batch Operations
- [ ] **Bulk Actions**
  - `complete_multiple_todos` tool
  - `delete_multiple_todos` tool
  - `bulk_add_todos` for importing lists

### Configuration & Usability
- [ ] **Configuration Management**
  - Environment variable for todo file location
  - Configuration file support (JSON/YAML)
  - Default settings with override capability

- [ ] **Data Export/Import**
  - Export todos to JSON/CSV formats
  - Import from external todo formats
  - Backup and restore functionality

- [ ] **Advanced Querying**
  - Sort todos by created_at, completed_at, priority
  - Pagination support for large todo lists
  - Statistics: completed vs pending count

### Code Quality Improvements
- [ ] **Error Handling**
  - Specific exception classes for different error types
  - Better error messages for MCP clients
  - Validation error details

- [x] **Testing** ✅ **COMPLETED**
  - ✅ Unit tests for all tools (16 tests implemented)
  - ✅ Integration tests for file operations  
  - ✅ Edge case testing (non-existent IDs, empty files, etc.)
  - [ ] Security test cases for malicious inputs (still needed)
  - [ ] Performance tests for large todo lists
  - [ ] Code coverage reporting

- [ ] **Documentation**
  - Add docstrings for all functions
  - MCP tool schema documentation
  - Usage examples for each tool

### Performance Optimizations
- [ ] **Caching**
  - In-memory caching of todo data
  - File modification time checking
  - Lazy loading for large todo lists

- [ ] **Data Structure**
  - Consider SQLite for better performance with large datasets
  - Indexing for faster searches
  - Data migration utilities

## Implementation Priority

1. **Immediate (Security Critical)**
   - YAML safe loading
   - Input validation
   - File permissions

2. **Short Term (Core Features)**
   - Search functionality
   - Priority system
   - Configuration support

3. **Medium Term (Enhanced Features)**
   - Tags and categories
   - Due dates
   - Bulk operations

4. **Long Term (Advanced Features)**
   - Database migration
   - Advanced querying
   - Performance optimizations

## Testing Status

### ✅ Completed (January 2025)
**Comprehensive test suite implemented with 16 tests covering:**

- **Helper Functions** (5 tests):
  - `load_todos()`: File not exists, empty file, valid data scenarios  
  - `save_todos()`: Atomic write operations
  - `current_timestamp()`: ISO 8601 format validation

- **MCP Tools** (9 tests):
  - `list_todos()`: Empty list handling
  - `add_todo()`: Single and multiple todo creation
  - `complete_todo()`: Existing and non-existent ID handling
  - `delete_todo()`: Proper cleanup and error cases
  - `get_timestamp()`: Utility function validation

- **Integration Tests** (2 tests):
  - Complete workflow: create → complete → delete
  - Data persistence across load/save operations

**Test Infrastructure:**
- Isolated test environment with temporary files
- Proper setup/teardown for each test case
- Direct function testing without MCP server dependency
- All tests pass with 100% success rate

### 🎯 Next Testing Priorities
1. Security test cases for malicious YAML inputs
2. Performance tests with large datasets (1000+ todos)
3. Concurrent access testing
4. Input validation boundary testing
5. Code coverage measurement

## Notes
- Maintain backward compatibility with existing YAML structure
- Consider semantic versioning for data format changes
- Add migration scripts for breaking changes
- Test coverage provides confidence for future refactoring