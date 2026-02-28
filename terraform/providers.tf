terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.62.0"
    }
  }
}

provider "azurerm" {
  features {}
  use_oidc = true
}
