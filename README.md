# heidi-todoist

Azure Function http trigger for marking a Todoist task complete and creating a new task 4.5 hours later.

# Usage

Request:
```shell
curl --location 'http:///api/completeTask' \
--header 'Content-Type: application/json' \
--data '{
    "task_name": "Outside"
}' 
```

# License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.