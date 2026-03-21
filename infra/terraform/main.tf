# ──────────────────────────────────────────────
# SelfDiary — Terraform Infrastructure
# ──────────────────────────────────────────────
# Provisions AWS resources for staging/production:
#   - VPC with public/private subnets
#   - RDS PostgreSQL 16 with automated backups
#   - S3 bucket for attachments
#   - ECS Fargate cluster for API + Web
#   - ALB for load balancing
#   - Secrets Manager for sensitive configuration
#
# Usage:
#   cd infra/terraform
#   terraform init
#   terraform plan -var-file=staging.tfvars
#   terraform apply -var-file=staging.tfvars
# ──────────────────────────────────────────────

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }

  backend "s3" {
    bucket         = "selfdiary-terraform-state"
    key            = "state/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "selfdiary-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "SelfDiary"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
