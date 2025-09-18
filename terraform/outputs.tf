output "function_app_name" {
  value = azurerm_linux_function_app.main.name
}

output "python_version" {
  value       = azurerm_linux_function_app.main.site_config[0].application_stack[0].python_version
  description = "The Python version configured for the app service"
}
