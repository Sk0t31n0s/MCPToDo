"""
Unit tests for Todo List Manager MCP Server
"""

import os
import tempfile
import uuid
import logging
from datetime import datetime
from pathlib import Path
from unittest import mock
import pytest

# We'll test the functions directly without importing the main module
# to avoid MCP server initialization issues
import sys
sys.path.insert(0, '.')

# Import specific functions we want to test
from main import load_todos, save_todos, current_timestamp, add_todo, complete_todo, delete_todo, list_todos, get_timestamp, setup_logging, logger


class TestHelperFunctions:
    """Test helper functions in main.py"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_todos.yaml"
        
        # Mock the TODO_FILE to use our test file
        import main
        self.original_todo_file = main.TODO_FILE
        main.TODO_FILE = self.test_file
    
    def teardown_method(self):
        """Clean up after each test"""
        # Restore original TODO_FILE
        import main
        main.TODO_FILE = self.original_todo_file
        
        # Clean up test file if it exists
        if self.test_file.exists():
            self.test_file.unlink()
        
        # Remove temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_todos_file_not_exists(self):
        """Test loading todos when file doesn't exist"""
        result = load_todos()
        assert result == {"todos": []}
    
    def test_load_todos_empty_file(self):
        """Test loading todos from empty file"""
        # Create empty file
        self.test_file.touch()
        result = load_todos()
        assert result == {"todos": []}
    
    def test_load_todos_valid_data(self):
        """Test loading valid todo data"""
        # Create test data
        test_data = {
            "todos": [
                {
                    "id": "test-id",
                    "description": "Test todo",
                    "status": "pending",
                    "created_at": "2025-01-01T12:00:00",
                    "completed_at": None
                }
            ]
        }
        
        # Write test data to file
        import main
        with open(self.test_file, "w") as f:
            main.yaml.dump(test_data, f)
        
        result = load_todos()
        assert result == test_data
    
    def test_save_todos(self):
        """Test saving todos to file"""
        test_data = {
            "todos": [
                {
                    "id": "save-test-id",
                    "description": "Save test todo",
                    "status": "pending",
                    "created_at": "2025-01-01T12:00:00",
                    "completed_at": None
                }
            ]
        }
        
        save_todos(test_data)
        
        # Verify file was created and contains correct data
        assert self.test_file.exists()
        loaded_data = load_todos()
        assert loaded_data == test_data
    
    def test_file_permissions(self):
        """Test that saved files have secure permissions (600)"""
        test_data = {"todos": []}
        save_todos(test_data)
        
        # Check file permissions (should be 600 = rw-------)
        file_stat = self.test_file.stat()
        file_mode = file_stat.st_mode & 0o777  # Get permission bits
        assert file_mode == 0o600, f"Expected 600 permissions, got {oct(file_mode)}"
    
    def test_current_timestamp_format(self):
        """Test that current_timestamp returns valid ISO format"""
        timestamp = current_timestamp()
        
        # Should be able to parse as datetime
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)
        
        # Should match expected format (no microseconds)
        assert len(timestamp) == 19  # YYYY-MM-DDTHH:MM:SS


class TestMCPTools:
    """Test MCP tool functions"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_todos.yaml"
        
        # Mock the TODO_FILE to use our test file
        import main
        self.original_todo_file = main.TODO_FILE
        main.TODO_FILE = self.test_file
    
    def teardown_method(self):
        """Clean up after each test"""
        # Restore original TODO_FILE
        import main
        main.TODO_FILE = self.original_todo_file
        
        # Clean up test file if it exists
        if self.test_file.exists():
            self.test_file.unlink()
        
        # Remove temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_list_todos_empty(self):
        """Test listing todos when none exist"""
        result = list_todos()
        assert result == []
    
    def test_add_todo(self):
        """Test adding a new todo"""
        description = "Test todo item"
        result = add_todo(description)
        
        # Verify return structure
        assert "id" in result
        assert result["description"] == description
        assert result["status"] == "pending"
        assert result["created_at"] is not None
        assert result["completed_at"] is None
        
        # Verify UUID format
        assert isinstance(uuid.UUID(result["id"]), uuid.UUID)
        
        # Verify it was saved
        todos = list_todos()
        assert len(todos) == 1
        assert todos[0] == result
    
    def test_add_multiple_todos(self):
        """Test adding multiple todos"""
        descriptions = ["Todo 1", "Todo 2", "Todo 3"]
        
        for desc in descriptions:
            add_todo(desc)
        
        todos = list_todos()
        assert len(todos) == 3
        
        # Verify all descriptions are present
        todo_descriptions = [todo["description"] for todo in todos]
        assert set(todo_descriptions) == set(descriptions)
    
    def test_complete_todo_existing(self):
        """Test completing an existing todo"""
        # Add a todo first
        added_todo = add_todo("Todo to complete")
        todo_id = added_todo["id"]
        
        # Complete it
        result = complete_todo(todo_id)
        
        # Verify return value
        assert result is not None
        assert result["id"] == todo_id
        assert result["status"] == "done"
        assert result["completed_at"] is not None
        assert result["description"] == "Todo to complete"
        
        # Verify it was updated in storage
        todos = list_todos()
        assert len(todos) == 1
        assert todos[0]["status"] == "done"
        assert todos[0]["completed_at"] is not None
    
    def test_complete_todo_nonexistent(self):
        """Test completing a non-existent todo"""
        fake_id = str(uuid.uuid4())
        result = complete_todo(fake_id)
        assert result is None
    
    def test_delete_todo_existing(self):
        """Test deleting an existing todo"""
        # Add a todo first
        added_todo = add_todo("Todo to delete")
        todo_id = added_todo["id"]
        
        # Delete it
        result = delete_todo(todo_id)
        assert result is True
        
        # Verify it was removed
        todos = list_todos()
        assert len(todos) == 0
    
    def test_delete_todo_nonexistent(self):
        """Test deleting a non-existent todo"""
        fake_id = str(uuid.uuid4())
        result = delete_todo(fake_id)
        assert result is False
    
    def test_delete_todo_with_multiple(self):
        """Test deleting one todo when multiple exist"""
        # Add multiple todos
        todo1 = add_todo("Todo 1")
        todo2 = add_todo("Todo 2")
        todo3 = add_todo("Todo 3")
        
        # Delete middle one
        result = delete_todo(todo2["id"])
        assert result is True
        
        # Verify correct one was removed
        todos = list_todos()
        assert len(todos) == 2
        
        remaining_ids = [todo["id"] for todo in todos]
        assert todo1["id"] in remaining_ids
        assert todo3["id"] in remaining_ids
        assert todo2["id"] not in remaining_ids
    
    def test_get_timestamp(self):
        """Test get_timestamp tool"""
        timestamp = get_timestamp()
        
        # Should be able to parse as datetime
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)
        
        # Should be recent (within last minute)
        now = datetime.now()
        time_diff = abs((now - parsed).total_seconds())
        assert time_diff < 60


class TestLogging:
    """Test logging functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Clear any existing handlers
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
    
    def test_setup_logging_default(self):
        """Test default logging setup"""
        with mock.patch.dict(os.environ, {}, clear=True):
            setup_logging()
            
        # Should have at least one handler
        assert len(logger.handlers) >= 1
        assert logger.level == logging.INFO
    
    def test_setup_logging_debug_level(self):
        """Test logging setup with DEBUG level"""
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            setup_logging()
            
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file output"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            with mock.patch.dict(os.environ, {"LOG_FILE": log_file, "LOG_LEVEL": "INFO"}):
                setup_logging()
            
            # Should have console and file handlers
            assert len(logger.handlers) >= 2
            
            # Test that logging to file works
            logger.info("Test log message")
            
            with open(log_file, 'r') as f:
                content = f.read()
                assert "Test log message" in content
                
        finally:
            # Cleanup
            try:
                os.unlink(log_file)
            except:
                pass
    
    def test_logging_in_mcp_functions(self):
        """Test that MCP functions generate appropriate log messages"""
        # Setup temp directory and file for test
        temp_dir = tempfile.mkdtemp()
        test_file = Path(temp_dir) / "test_todos.yaml"
        
        # Mock the TODO_FILE to use our test file
        import main
        original_todo_file = main.TODO_FILE
        main.TODO_FILE = test_file
        
        try:
            # Setup logging with a memory handler to capture logs
            import io
            log_stream = io.StringIO()
            handler = logging.StreamHandler(log_stream)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            # Test add_todo logging
            result = add_todo("Test todo for logging")
            log_output = log_stream.getvalue()
            
            assert "MCP Request: add_todo" in log_output
            assert "Test todo for logging" in log_output
            assert "MCP Response: add_todo created todo with ID" in log_output
            assert result["id"] in log_output
            
        finally:
            # Restore original TODO_FILE
            main.TODO_FILE = original_todo_file
            
            # Clean up test file and directory
            if test_file.exists():
                test_file.unlink()
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test_todos.yaml"
        
        # Mock the TODO_FILE to use our test file
        import main
        self.original_todo_file = main.TODO_FILE
        main.TODO_FILE = self.test_file
    
    def teardown_method(self):
        """Clean up after each test"""
        # Restore original TODO_FILE
        import main
        main.TODO_FILE = self.original_todo_file
        
        # Clean up test file if it exists
        if self.test_file.exists():
            self.test_file.unlink()
        
        # Remove temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test a complete todo management workflow"""
        # Start with empty list
        assert list_todos() == []
        
        # Add some todos
        todo1 = add_todo("Buy groceries")
        todo2 = add_todo("Walk the dog")
        todo3 = add_todo("Finish project")
        
        # Verify all were added
        todos = list_todos()
        assert len(todos) == 3
        
        # Complete one todo
        result = complete_todo(todo2["id"])
        assert result["status"] == "done"
        
        # Verify status in list
        todos = list_todos()
        completed_todos = [t for t in todos if t["status"] == "done"]
        pending_todos = [t for t in todos if t["status"] == "pending"]
        assert len(completed_todos) == 1
        assert len(pending_todos) == 2
        assert completed_todos[0]["id"] == todo2["id"]
        
        # Delete a todo
        assert delete_todo(todo1["id"]) is True
        
        # Verify final state
        todos = list_todos()
        assert len(todos) == 2
        remaining_ids = [t["id"] for t in todos]
        assert todo2["id"] in remaining_ids
        assert todo3["id"] in remaining_ids
        assert todo1["id"] not in remaining_ids
    
    def test_data_persistence(self):
        """Test that data persists across load/save operations"""
        # Add a todo
        original_todo = add_todo("Persistent todo")
        
        # Simulate server restart by reloading data
        loaded_data = load_todos()
        assert len(loaded_data["todos"]) == 1
        assert loaded_data["todos"][0]["id"] == original_todo["id"]
        assert loaded_data["todos"][0]["description"] == "Persistent todo"
        
        # Complete the todo and save
        complete_todo(original_todo["id"])
        
        # Reload and verify completion persisted
        reloaded_data = load_todos()
        assert reloaded_data["todos"][0]["status"] == "done"
        assert reloaded_data["todos"][0]["completed_at"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])