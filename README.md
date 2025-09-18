# heidi-todoist

Azure Function http trigger for marking a Todoist task complete and creating a new task 4.5 hours later.

# Usage

Request:
```shell
curl -X POST \
--location 'https://{your-function-app-name}.azurewebsites.net/api/completeTask?code={your-function-access-key}' \
--header 'Content-Type: application/json' \
--data '{
    "task_name": "{your-task-name}"
}' 
```

Response:
```json5
{
    "success": true,
    "message": "Task \"{your-task-name}\" completed and recreated",
    "new_task_id": "{todoist-new-task-id}",
    "new_due_time": "2025-01-01T18:00:00",  // 4.5 hours after current time (or 08:30:00 if new time is earlier than 8:30am)
    "completed_task_id": "{todoist-old-task-id}"
}
```

# License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.