import os
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import requests
from heidi_todoist.services import TodoistService


class TestTodoistService:
    """Test cases for TodoistService class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock environment variable and TodoistAPI
        with patch.dict(os.environ, {'TODOIST_API_TOKEN': 'test_token'}):
            with patch('heidi_todoist.services.TodoistAPI') as mock_api_class:
                self.mock_api = Mock()
                mock_api_class.return_value = self.mock_api
                self.service = TodoistService()

    def test_init_with_token(self):
        """Test successful initialization with valid token."""
        with patch.dict(os.environ, {'TODOIST_API_TOKEN': 'test_token'}):
            service = TodoistService()
            assert service.api is not None
            assert service.logger is not None

    def test_init_without_token(self):
        """Test initialization fails without token."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match='TODOIST_API_TOKEN environment variable not set'):
                TodoistService()

    def test_calculate_next_due_time_normal(self):
        """Test next due time calculation for normal hours."""
        with patch('heidi_todoist.services.datetime') as mock_datetime:
            # Mock current time as 10:00 AM
            mock_now = datetime(2023, 1, 1, 10, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = self.service._calculate_next_due_time()

            # Should be 4.5 hours later (2:30 PM)
            expected = "2023-01-01T14:30:00"
            assert result == expected

    def test_calculate_next_due_time_early_morning(self):
        """Test next due time calculation when result would be before 8:30 AM."""
        with patch('heidi_todoist.services.datetime') as mock_datetime:
            # Mock current time as 2:00 AM
            mock_now = datetime(2023, 1, 1, 2, 0, 0)
            mock_datetime.now.return_value = mock_now

            result = self.service._calculate_next_due_time()

            # Should be set to 8:30 AM instead of 6:30 AM
            expected = "2023-01-01T08:30:00"
            assert result == expected

    def test_calculate_next_due_time_exactly_eight_twenty_nine(self):
        """Test next due time calculation when result is exactly 8:29 AM."""
        with patch('heidi_todoist.services.datetime') as mock_datetime:
            # Mock current time such that 4.5 hours later is 8:29 AM
            mock_now = datetime(2023, 1, 1, 3, 59, 0)  # 3:59 AM + 4.5h = 8:29 AM
            mock_datetime.now.return_value = mock_now

            result = self.service._calculate_next_due_time()

            # Should be set to 8:30 AM
            expected = "2023-01-01T08:30:00"
            assert result == expected

    def test_extract_project_id_with_dash(self):
        """Test project ID extraction from formatted string."""
        project_id = "heidi-6cvcJh2HrqCMxvcF"
        result = self.service._extract_project_id(project_id)
        assert result == "6cvcJh2HrqCMxvcF"

    def test_extract_project_id_without_dash(self):
        """Test project ID extraction from plain string."""
        project_id = "12345"
        result = self.service._extract_project_id(project_id)
        assert result == "12345"

    def test_extract_project_id_multiple_dashes(self):
        """Test project ID extraction with multiple dashes."""
        project_id = "project-name-with-dashes-12345"
        result = self.service._extract_project_id(project_id)
        assert result == "12345"

    @patch('heidi_todoist.services.datetime')
    def test_complete_and_recreate_task_success_existing_task(self, mock_datetime):
        """Test successful completion and recreation with existing task."""
        # Mock datetime
        mock_now = datetime(2023, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.return_value = datetime(2023, 1, 1, 14, 30, 0)

        # Mock existing task
        mock_task = Mock()
        mock_task.content = "Test Task"
        mock_task.id = "task123"

        # Mock API responses
        self.mock_api.get_tasks.return_value = iter([[mock_task]])
        self.mock_api.complete_task.return_value = True

        mock_new_task = Mock()
        mock_new_task.id = "new_task456"
        self.mock_api.add_task.return_value = mock_new_task

        result = self.service.complete_and_recreate_task("project123", "Test Task")

        assert result['success'] is True
        assert result['completed_task_id'] == "task123"
        assert result['new_task_id'] == "new_task456"
        assert "Test Task" in result['message']
        assert "completed and recreated" in result['message']

    @patch('heidi_todoist.services.datetime')
    def test_complete_and_recreate_task_no_existing_task(self, mock_datetime):
        """Test creation without existing task to complete."""
        # Mock datetime
        mock_now = datetime(2023, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.return_value = datetime(2023, 1, 1, 14, 30, 0)

        # Mock no existing tasks
        self.mock_api.get_tasks.return_value = iter([[]])

        mock_new_task = Mock()
        mock_new_task.id = "new_task456"
        self.mock_api.add_task.return_value = mock_new_task

        result = self.service.complete_and_recreate_task("project123", "New Task")

        assert result['success'] is True
        assert 'completed_task_id' not in result
        assert result['new_task_id'] == "new_task456"
        assert "no existing task found" in result['message']

    @patch('heidi_todoist.services.datetime')
    def test_complete_and_recreate_task_complete_fails(self, mock_datetime):
        """Test when task completion fails but recreation succeeds."""
        # Mock datetime
        mock_now = datetime(2023, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.return_value = datetime(2023, 1, 1, 14, 30, 0)

        # Mock existing task
        mock_task = Mock()
        mock_task.content = "Test Task"
        mock_task.id = "task123"

        # Mock API responses - completion fails
        self.mock_api.get_tasks.return_value = iter([[mock_task]])
        self.mock_api.complete_task.return_value = False

        mock_new_task = Mock()
        mock_new_task.id = "new_task456"
        self.mock_api.add_task.return_value = mock_new_task

        result = self.service.complete_and_recreate_task("project123", "Test Task")

        assert result['success'] is True
        assert 'completed_task_id' not in result
        assert result['new_task_id'] == "new_task456"

    def test_complete_and_recreate_task_http_400_error(self):
        """Test handling of 400 Bad Request error."""
        # Mock HTTP 400 error
        mock_response = Mock()
        mock_response.status_code = 400
        http_error = requests.exceptions.HTTPError("Bad Request")
        http_error.response = mock_response

        self.mock_api.get_tasks.side_effect = http_error

        result = self.service.complete_and_recreate_task("project123", "Test Task")

        assert result['success'] is False
        assert "Invalid project_id format" in result['error']
        assert result['completed_task_id'] is None
        assert result['created_task_id'] is None

    def test_complete_and_recreate_task_http_other_error(self):
        """Test handling of other HTTP errors."""
        # Mock HTTP 500 error
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("Internal Server Error")
        http_error.response = mock_response

        self.mock_api.get_tasks.side_effect = http_error

        result = self.service.complete_and_recreate_task("project123", "Test Task")

        assert result['success'] is False
        assert "API error" in result['error']
        assert result['completed_task_id'] is None
        assert result['created_task_id'] is None

    def test_complete_and_recreate_task_request_exception(self):
        """Test handling of general request exceptions."""
        # Mock general request exception
        self.mock_api.get_tasks.side_effect = requests.exceptions.RequestException("Network error")

        result = self.service.complete_and_recreate_task("project123", "Test Task")

        assert result['success'] is False
        assert "API request error" in result['error']
        assert result['completed_task_id'] is None
        assert result['created_task_id'] is None

    def test_complete_and_recreate_task_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        # Mock unexpected exception
        self.mock_api.get_tasks.side_effect = Exception("Unexpected error")

        result = self.service.complete_and_recreate_task("project123", "Test Task")

        assert result['success'] is False
        assert "Unexpected error" in result['error']
        assert result['completed_task_id'] is None
        assert result['created_task_id'] is None

    @patch('heidi_todoist.services.datetime')
    def test_complete_and_recreate_task_multiple_task_batches(self, mock_datetime):
        """Test finding task across multiple batches from iterator."""
        # Mock datetime
        mock_now = datetime(2023, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.return_value = datetime(2023, 1, 1, 14, 30, 0)

        # Mock tasks in different batches
        mock_task1 = Mock()
        mock_task1.content = "Other Task"
        mock_task1.id = "other123"

        mock_task2 = Mock()
        mock_task2.content = "Target Task"
        mock_task2.id = "target123"

        # Return multiple batches
        self.mock_api.get_tasks.return_value = iter([[mock_task1], [mock_task2]])
        self.mock_api.complete_task.return_value = True

        mock_new_task = Mock()
        mock_new_task.id = "new_task456"
        self.mock_api.add_task.return_value = mock_new_task

        result = self.service.complete_and_recreate_task("project123", "Target Task")

        assert result['success'] is True
        assert result['completed_task_id'] == "target123"
        assert result['new_task_id'] == "new_task456"

    @patch('heidi_todoist.services.datetime')
    def test_complete_and_recreate_task_calls_extract_project_id(self, mock_datetime):
        """Test that project ID extraction is called properly."""
        # Mock datetime
        mock_now = datetime(2023, 1, 1, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.return_value = datetime(2023, 1, 1, 14, 30, 0)

        # Mock no existing tasks
        self.mock_api.get_tasks.return_value = iter([[]])

        mock_new_task = Mock()
        mock_new_task.id = "new_task456"
        self.mock_api.add_task.return_value = mock_new_task

        # Spy on the extract method
        with patch.object(self.service, '_extract_project_id', return_value='extracted123') as mock_extract:
            result = self.service.complete_and_recreate_task("original-project-123", "Test Task")

            mock_extract.assert_called_once_with("original-project-123")

            # Verify the extracted project_id was used
            self.mock_api.get_tasks.assert_called_once_with(project_id='extracted123')
            self.mock_api.add_task.assert_called_once()
            add_task_call = self.mock_api.add_task.call_args
            assert add_task_call.kwargs['project_id'] == 'extracted123'