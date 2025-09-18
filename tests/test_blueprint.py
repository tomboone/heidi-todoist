import os
import json
import pytest
from unittest.mock import Mock, patch
import azure.functions as func
from heidi_todoist.blueprint import complete_task


class TestBlueprint:
    """Test cases for the blueprint module."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Clear any existing environment variables
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

    def teardown_method(self):
        """Clean up after each test method."""
        self.env_patcher.stop()

    def test_complete_task_success(self):
        """Test successful task completion and recreation."""
        # Set up environment
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            # Mock request with JSON body
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'task_name': 'Test Task'}

            # Mock TodoistService
            with patch('heidi_todoist.blueprint.TodoistService') as mock_service_class:
                mock_service = Mock()
                mock_service.complete_and_recreate_task.return_value = {
                    'success': True,
                    'completed_task_id': 'old_123',
                    'new_task_id': 'new_456',
                    'message': 'Task "Test Task" completed and recreated',
                    'new_due_time': '2023-01-01T14:30:00'
                }
                mock_service_class.return_value = mock_service

                response = complete_task(mock_req)

                # Verify response
                assert response.status_code == 200
                assert response.mimetype == "application/json"

                response_data = json.loads(response.get_body())
                assert response_data['success'] is True
                assert response_data['completed_task_id'] == 'old_123'
                assert response_data['new_task_id'] == 'new_456'

                # Verify service was called correctly
                mock_service.complete_and_recreate_task.assert_called_once_with('test_project_123', 'Test Task')

    def test_complete_task_missing_project_id(self):
        """Test error when HEIDI_PROJECT_ID is not configured."""
        # Don't set HEIDI_PROJECT_ID environment variable
        mock_req = Mock(spec=func.HttpRequest)
        mock_req.get_json.return_value = {'task_name': 'Test Task'}

        response = complete_task(mock_req)

        assert response.status_code == 500
        assert response.mimetype == "application/json"

        response_data = json.loads(response.get_body())
        assert response_data['success'] is False
        assert 'HEIDI_PROJECT_ID not configured' in response_data['error']

    def test_complete_task_missing_task_name_no_json(self):
        """Test error when request has no JSON body."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = None

            response = complete_task(mock_req)

            assert response.status_code == 400
            assert response.mimetype == "application/json"

            response_data = json.loads(response.get_body())
            assert response_data['success'] is False
            assert 'task_name is required in JSON body' in response_data['error']

    def test_complete_task_missing_task_name_empty_json(self):
        """Test error when JSON body doesn't contain task_name."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'other_field': 'value'}

            response = complete_task(mock_req)

            assert response.status_code == 400
            assert response.mimetype == "application/json"

            response_data = json.loads(response.get_body())
            assert response_data['success'] is False
            assert 'task_name is required in JSON body' in response_data['error']

    def test_complete_task_invalid_json(self):
        """Test error when request contains invalid JSON."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.side_effect = ValueError("Invalid JSON")

            response = complete_task(mock_req)

            assert response.status_code == 400
            assert response.mimetype == "application/json"

            response_data = json.loads(response.get_body())
            assert response_data['success'] is False
            assert 'task_name is required in JSON body' in response_data['error']

    def test_complete_task_json_attribute_error(self):
        """Test error when request object doesn't have get_json method."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.side_effect = AttributeError("No get_json method")

            response = complete_task(mock_req)

            assert response.status_code == 400
            assert response.mimetype == "application/json"

            response_data = json.loads(response.get_body())
            assert response_data['success'] is False
            assert 'task_name is required in JSON body' in response_data['error']

    def test_complete_task_service_failure(self):
        """Test handling when TodoistService operation fails."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'task_name': 'Test Task'}

            with patch('heidi_todoist.blueprint.TodoistService') as mock_service_class:
                mock_service = Mock()
                mock_service.complete_and_recreate_task.return_value = {
                    'success': False,
                    'error': 'API connection failed',
                    'completed_task_id': None,
                    'created_task_id': None
                }
                mock_service_class.return_value = mock_service

                response = complete_task(mock_req)

                assert response.status_code == 500
                assert response.mimetype == "application/json"

                response_data = json.loads(response.get_body())
                assert response_data['success'] is False
                assert response_data['error'] == 'API connection failed'

    def test_complete_task_service_not_found_error(self):
        """Test handling when service returns 'not found' error."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'task_name': 'Test Task'}

            with patch('heidi_todoist.blueprint.TodoistService') as mock_service_class:
                mock_service = Mock()
                mock_service.complete_and_recreate_task.return_value = {
                    'success': False,
                    'error': 'Task not found in project',
                    'completed_task_id': None,
                    'created_task_id': None
                }
                mock_service_class.return_value = mock_service

                response = complete_task(mock_req)

                assert response.status_code == 404
                assert response.mimetype == "application/json"

                response_data = json.loads(response.get_body())
                assert response_data['success'] is False
                assert 'not found' in response_data['error']

    def test_complete_task_value_error_exception(self):
        """Test handling of ValueError exception from TodoistService (missing API token)."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'task_name': 'Test Task'}

            response = complete_task(mock_req)

            assert response.status_code == 500
            assert response.mimetype == "application/json"

            response_data = json.loads(response.get_body())
            assert response_data['success'] is False
            assert 'TODOIST_API_TOKEN environment variable not set' in response_data['error']

    def test_complete_task_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123', 'TODOIST_API_TOKEN': 'test_token'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'task_name': 'Test Task'}

            # Mock the TodoistAPI constructor to avoid real API calls
            with patch('heidi_todoist.services.TodoistAPI'):
                with patch('heidi_todoist.blueprint.TodoistService') as mock_service_class:
                    mock_service_class.side_effect = Exception("Unexpected error")

                    # Mock logging to verify it's called
                    with patch('heidi_todoist.blueprint.logging') as mock_logging:
                        response = complete_task(mock_req)

                        assert response.status_code == 500
                        assert response.mimetype == "application/json"

                        response_data = json.loads(response.get_body())
                        assert response_data['success'] is False
                        assert response_data['error'] == 'Unexpected error'

                        # Verify logging was called
                        mock_logging.error.assert_called_once()

    def test_complete_task_empty_task_name(self):
        """Test error when task_name is empty string."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'task_name': ''}

            response = complete_task(mock_req)

            assert response.status_code == 400
            assert response.mimetype == "application/json"

            response_data = json.loads(response.get_body())
            assert response_data['success'] is False
            assert 'task_name is required in JSON body' in response_data['error']

    def test_complete_task_none_task_name(self):
        """Test error when task_name is None."""
        with patch.dict(os.environ, {'HEIDI_PROJECT_ID': 'test_project_123'}):
            mock_req = Mock(spec=func.HttpRequest)
            mock_req.get_json.return_value = {'task_name': None}

            response = complete_task(mock_req)

            assert response.status_code == 400
            assert response.mimetype == "application/json"

            response_data = json.loads(response.get_body())
            assert response_data['success'] is False
            assert 'task_name is required in JSON body' in response_data['error']