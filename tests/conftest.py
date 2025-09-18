"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_todoist_api():
    """Create a mock TodoistAPI instance."""
    api = Mock()
    api.get_tasks.return_value = iter([[]])
    api.complete_task.return_value = True
    api.add_task.return_value = Mock(id="test_task_123")
    return api


@pytest.fixture
def mock_http_request():
    """Create a mock Azure Functions HttpRequest."""
    request = Mock()
    request.get_json.return_value = {'task_name': 'Test Task'}
    return request