variable "service_plan_name" {
  type = string
  description = "Name of the existing app service plan to use"
}

variable "service_plan_rg_name" {
  type = string
  description = "Resource group for the existing app service plan"
}

variable "log_analytics_workspace_name" {
  type = string
  description = "Name of the existing log analytics workspace to use"
}

variable "log_analytics_workspace_rg_name" {
  type = string
  description = "Resource group for the existing log analytics workspace"
}

variable "todoist_api_token" {
  type = string
  description = "Todoist account dveloper API token"
  sensitive = true
}

variable "heidi_project_id" {
  type = string
  description = "ID portion of Todoist's project URL to manage tasks for"
}