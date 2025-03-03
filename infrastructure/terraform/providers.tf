# Terraform required version and provider configurations
terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
    template = {
      source  = "hashicorp/template"
      version = "~> 2.2"
    }
  }
}

# Primary AWS provider configuration
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "InteractionManagement"
      ManagedBy   = "Terraform"
    }
  }
}

# Secondary AWS provider configuration for multi-AZ deployment
provider "aws" {
  alias   = "secondary"
  region  = var.aws_secondary_region
  profile = var.aws_profile
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "InteractionManagement"
      ManagedBy   = "Terraform"
    }
  }
}

# Random provider for generating secure resource names
provider "random" {}

# Time provider for time-based operations
provider "time" {}

# Template provider for configuration file generation
provider "template" {}