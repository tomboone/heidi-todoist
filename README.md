# heidi-todoist

Azure Function http trigger for marking a Todoist task complete and creating a new task 4.5 hours later.

## Environment variables

Required:

* **TODOIST_API_TOKEN** - Your Todoist account's API token
* **HEIDI_PROJECT_ID** - The ID portion of the project URL (not the actual project ID returned by the API)

Optional:

* **TIMEZONE** - PyTZ/IANA database [time zone (TZ) identifier](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List) (defaults to 'America/New_York')

## Usage

Request:
```shell
curl -X POST \
--location 'https://{function-name}.azurewebsites.net/api/completeTask?code={function-key}' \
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
    "new_due_time": "2025-01-01T18:00:00",  // 4.5 hours after current time
    "completed_task_id": "{todoist-old-task-id}"
}
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.