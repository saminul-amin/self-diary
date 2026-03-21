# SelfDiary — Infrastructure

Production infrastructure-as-code and configuration.

## Contents

| Directory    | Purpose                                                   |
| ------------ | --------------------------------------------------------- |
| `terraform/` | AWS infrastructure (VPC, ECS Fargate, RDS, S3, ALB, etc.) |
| `nginx/`     | Nginx reverse proxy with TLS, rate limiting, gzip         |

## Terraform Quick Start

```bash
cd infra/terraform

# Initialise (first time)
terraform init

# Plan against staging
terraform plan -var-file=staging.tfvars

# Apply
terraform apply -var-file=staging.tfvars

# Production
terraform plan -var-file=production.tfvars
terraform apply -var-file=production.tfvars
```

### Prerequisites

- Terraform >= 1.7
- AWS CLI configured with appropriate IAM permissions
- S3 bucket `selfdiary-terraform-state` and DynamoDB table `selfdiary-terraform-locks` created for remote state

### Environment Files

| File                | Purpose                   |
| ------------------- | ------------------------- |
| `staging.tfvars`    | Staging env overrides     |
| `production.tfvars` | Production env overrides  |

## Architecture

```
Internet → ALB (public subnets)
            ├── /v1/* → API (ECS Fargate, private subnets)
            └── /*    → Web (ECS Fargate, private subnets)

API → RDS PostgreSQL (private subnets)
API → S3 Attachments bucket
```
