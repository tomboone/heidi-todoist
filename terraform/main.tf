locals {
  service_name = "heidi-todoist"
}

data "azurerm_service_plan" "existing" {
  name                = var.service_plan_name
  resource_group_name = var.service_plan_rg_name
}

data "azurerm_log_analytics_workspace" "existing" {
  name                = var.log_analytics_workspace_name
  resource_group_name = var.log_analytics_workspace_rg_name
}

resource "azurerm_resource_group" "main" {
  name     = "${ local.service_name }-rg"
  location = data.azurerm_service_plan.existing.location
}

resource "azurerm_storage_account" "main" {
  name                     = "${ replace(local.service_name, "-", "") }sa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = data.azurerm_service_plan.existing.location
  account_replication_type = "LRS"
  account_tier             = "Standard"
}

resource "azurerm_application_insights" "main" {
  name                = "${ local.service_name }-insights"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  workspace_id        = data.azurerm_log_analytics_workspace.existing.id
  application_type    = "web"
}

resource "azurerm_linux_function_app" "main" {
  name                       = local.service_name
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location

  service_plan_id            = data.azurerm_service_plan.existing.id

  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

  https_only                 = true

  site_config {
    always_on = true
    application_insights_connection_string = azurerm_application_insights.main.connection_string
    application_insights_key = azurerm_application_insights.main.instrumentation_key
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"              = "1"
    "TODOIST_API_TOKEN"                     = var.todoist_api_token
    "HEIDI_PROJECT_ID"                      = var.heidi_project_id
  }
}
