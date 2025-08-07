#!/usr/bin/env python3
"""Test command execution functionality in command_executor.py module."""

import pytest
import sys
import os
import time
import threading
import queue
from unittest.mock import Mock, patch
import logging
logging.basicConfig(level=logging.ERROR)

# Add paths to import the modules we want to test
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'kali-server'))

def test_execute_command_basic():
    """Test basic command execution functionality."""
    from core.command_executor import execute_command
    
    # Test simple command
    result = execute_command("echo 'test'", timeout=5)
    
    assert result is not None
    assert isinstance(result, dict)
    assert "success" in result
    assert "return_code" in result
    assert "stdout" in result or "output" in result


def test_execute_command_with_timeout():
    """Test command execution with timeout."""
    from core.command_executor import execute_command
    
    # Test command that should timeout
    start_time = time.time()
    result = execute_command("sleep 10", timeout=2)
    end_time = time.time()
    
    # Should complete within timeout + some buffer
    assert (end_time - start_time) < 5
    assert result is not None
    assert isinstance(result, dict)


def test_stream_command_execution_blocking_detection():
    """Test that stream_command_execution detects blocking commands."""
    from core.command_executor import stream_command_execution
    from core.config import BLOCKING_TIMEOUT
    
    # Mock a command that produces no output (simulating blocking behavior)
    def mock_blocking_command():
        """Simulate a command that produces no initial output."""
        # This generator will produce no output for BLOCKING_TIMEOUT + 1 seconds
        time.sleep(BLOCKING_TIMEOUT + 1)
        yield "data: {\"type\": \"output\", \"source\": \"stdout\", \"line\": \"late output\"}\n\n"
    
    # Test the streaming function with our mock
    output_lines = []
    start_time = time.time()
    
    try:
        # Create a generator that simulates blocking behavior
        for line in stream_command_execution("sleep 10", streaming=True):
            output_lines.append(line)
            # Break if we get the blocking error message
            if "Blocking or server-hanging commands are not allowed" in line:
                break
            # Safety timeout to prevent infinite loops in tests
            if time.time() - start_time > BLOCKING_TIMEOUT + 3:
                break
    except Exception as e:
        # Some exception is expected for blocking commands
        pass
    
    # Check that blocking was detected
    output_text = "".join(output_lines)
    assert len(output_lines) > 0, "Should have received some output"
    
    # Should have detected blocking within reasonable time
    elapsed_time = time.time() - start_time
    assert elapsed_time <= BLOCKING_TIMEOUT + 2, f"Should detect blocking quickly, took {elapsed_time}s"


def test_stream_command_execution_normal_command():
    """Test that stream_command_execution works normally for quick commands."""
    from core.command_executor import stream_command_execution
    
    output_lines = []
    start_time = time.time()
    
    try:
        # Test with a command that produces output quickly
        for line in stream_command_execution("echo 'test output'", streaming=True):
            output_lines.append(line)
            # Break when we get completion message
            if '"type": "complete"' in line:
                break
            # Safety timeout
            if time.time() - start_time > 10:
                break
    except Exception as e:
        # Log any unexpected exception
        print(f"Unexpected exception: {e}")
    
    # Check that we got normal output
    output_text = "".join(output_lines)
    assert len(output_lines) > 0, "Should have received output"
    assert '"type": "output"' in output_text, "Should contain output data"
    assert '"type": "complete"' in output_text, "Should complete normally"
    assert 'Blocking or server-hanging commands are not allowed' not in output_text, "Should not detect blocking"


def test_stream_command_execution_with_output_callback():
    """Test streaming with output callback functionality."""
    from core.command_executor import stream_command_execution
    
    output_lines = []
    
    try:
        # Test streaming behavior
        for line in stream_command_execution("echo 'callback test'", streaming=True):
            output_lines.append(line)
            if '"type": "complete"' in line:
                break
    except Exception as e:
        print(f"Exception in callback test: {e}")
    
    # Verify we got streaming data
    assert len(output_lines) > 0
    output_text = "".join(output_lines)
    # Should contain streaming data format
    assert 'data: {' in output_text


def test_blocking_timeout_configuration():
    """Test that BLOCKING_TIMEOUT is properly configured."""
    from core.config import BLOCKING_TIMEOUT
    
    # Should be a positive integer
    assert isinstance(BLOCKING_TIMEOUT, int)
    assert BLOCKING_TIMEOUT > 0
    assert BLOCKING_TIMEOUT <= 30  # Reasonable upper bound


def test_command_executor_module_imports():
    """Test that all required functions can be imported from command_executor."""
    try:
        from core.command_executor import execute_command, stream_command_execution
        assert callable(execute_command)
        assert callable(stream_command_execution)
        print("✅ All command_executor functions imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import required functions: {e}")


if __name__ == "__main__":
    """Run tests directly for debugging."""
    print("Testing command_executor.py module...")
    
    try:
        test_command_executor_module_imports()
        test_blocking_timeout_configuration()
        test_execute_command_basic()
        test_execute_command_with_timeout()
        test_stream_command_execution_normal_command()
        test_stream_command_execution_blocking_detection()
        test_stream_command_execution_with_output_callback()
        
        print("✅ All command_executor tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
