import azure.functions as func
import json
import logging
import os
from heidi_todoist.services import TodoistService

bp = func.Blueprint()


@bp.route(route="completeTask", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    """Complete a task by name in the Heidi project."""

    try:
        # Get project ID from environment
        project_id = os.environ.get('HEIDI_PROJECT_ID')
        if not project_id:
            return func.HttpResponse(
                json.dumps({'success': False, 'error': 'HEIDI_PROJECT_ID not configured'}),
                status_code=500,
                mimetype="application/json"
            )

        # Get task name from JSON body
        try:
            req_body = req.get_json()
            task_name = req_body.get('task_name') if req_body else None
        except (ValueError, AttributeError):
            task_name = None

        if not task_name:
            return func.HttpResponse(
                json.dumps({'success': False, 'error': 'task_name is required in JSON body'}),
                status_code=400,
                mimetype="application/json"
            )

        # Complete existing task and create new one
        service = TodoistService()
        result = service.complete_and_recreate_task(project_id, task_name)

        status_code = 200 if result['success'] else 404 if 'not found' in result.get('error', '') else 500

        return func.HttpResponse(
            json.dumps(result),
            status_code=status_code,
            mimetype="application/json"
        )

    except ValueError as e:
        return func.HttpResponse(
            json.dumps({'success': False, 'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}')
        return func.HttpResponse(
            json.dumps({'success': False, 'error': str(e)}),
            status_code=500,
            mimetype="application/json"
        )
