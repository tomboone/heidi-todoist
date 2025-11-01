terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.51.0"
    }
  }
}

provider "azurerm" {
  features {}
  use_oidc = true
}
