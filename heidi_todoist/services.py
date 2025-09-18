import os
import logging
from datetime import datetime, timedelta
import requests
from todoist_api_python.api import TodoistAPI


# noinspection PyMethodMayBeStatic
class TodoistService:
    """Minimal service class for completing and recreating Todoist tasks."""

    def __init__(self):
        token = os.environ.get('TODOIST_API_TOKEN')
        if not token:
            raise ValueError('TODOIST_API_TOKEN environment variable not set')

        self.api = TodoistAPI(token)
        self.logger = logging.getLogger(__name__)

    def _calculate_next_due_time(self) -> str:
        """Calculate the next due time: 4.5 hours from now, but not before 8:30am."""
        now = datetime.now()
        next_due = now + timedelta(hours=4.5)

        # If the calculated time is before 8:30am, set it to 8:30am
        if next_due.hour < 8 or (next_due.hour == 8 and next_due.minute < 30):
            next_due = next_due.replace(hour=8, minute=30, second=0, microsecond=0)

        # Format as ISO datetime string for Todoist API
        return next_due.strftime('%Y-%m-%dT%H:%M:%S')

    def _extract_project_id(self, project_id: str) -> str:
        """Extract or validate the project ID format."""
        # If project_id contains a dash, it might be formatted as "name-id"
        # Try to extract the part after the last dash
        if '-' in project_id:
            parts = project_id.split('-')
            # Return the last part which should be the actual ID
            potential_id = parts[-1]
            self.logger.info(f'Extracted potential project ID: {potential_id} from {project_id}')
            return potential_id

        # Return as-is if no dash found
        return project_id

    def complete_and_recreate_task(self, project_id: str, task_name: str) -> dict:
        """Complete a task by name and create a new one with the same name due in 4.5 hours."""
        completed_task_id = None
        created_task_id = None

        try:
            # Extract/validate project_id format
            actual_project_id = self._extract_project_id(project_id)
            self.logger.info(f'Using project_id: {actual_project_id} (original: {project_id})')

            # Step 1: Find and complete the existing task (if it exists)
            tasks_iterator = self.api.get_tasks(project_id=actual_project_id)

            target_task = None
            for task_batch in tasks_iterator:
                for task in task_batch:
                    if task.content == task_name:
                        target_task = task
                        break
                if target_task:
                    break

            if target_task:
                # Complete the existing task
                success = self.api.complete_task(task_id=target_task.id)
                if success:
                    completed_task_id = target_task.id
                    self.logger.info(f'Completed existing task: {target_task.id}')
                else:
                    self.logger.warning(f'Failed to complete existing task: {target_task.id}')
            else:
                self.logger.info(f'No existing task "{task_name}" found to complete')

            # Step 2: Create new task with calculated due time
            due_datetime = self._calculate_next_due_time()

            new_task = self.api.add_task(
                content=task_name,
                project_id=actual_project_id,
                due_datetime=datetime.fromisoformat(due_datetime)
            )

            created_task_id = new_task.id
            self.logger.info(f'Created new task: {new_task.id} due at {due_datetime}')

            # Prepare response
            response = {
                'success': True,
                'message': f'Task "{task_name}" completed and recreated',
                'new_task_id': created_task_id,
                'new_due_time': due_datetime
            }

            if completed_task_id:
                response['completed_task_id'] = completed_task_id
                response['message'] = f'Task "{task_name}" completed and recreated'
            else:
                response['message'] = f'Created new task "{task_name}" (no existing task found to complete)'

            return response

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                self.logger.error(f'Bad Request (400) - likely invalid project_id format: {project_id}. Error: {str(e)}')
                return {
                    'success': False,
                    'error': f'Invalid project_id format: {project_id}. Please check that the project ID is correct.',
                    'completed_task_id': completed_task_id,
                    'created_task_id': created_task_id
                }
            else:
                self.logger.error(f'Todoist API HTTP error: {str(e)}')
                return {
                    'success': False,
                    'error': f'API error: {str(e)}',
                    'completed_task_id': completed_task_id,
                    'created_task_id': created_task_id
                }
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Todoist API request error: {str(e)}')
            return {
                'success': False,
                'error': f'API request error: {str(e)}',
                'completed_task_id': completed_task_id,
                'created_task_id': created_task_id
            }
        except Exception as e:
            self.logger.error(f'Unexpected error: {str(e)}')
            return {
                'success': False,
                'error': str(e),
                'completed_task_id': completed_task_id,
                'created_task_id': created_task_id
            }
