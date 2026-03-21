# ─── General ───
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
}

variable "project_name" {
  description = "Project prefix for resource naming"
  type        = string
  default     = "selfdiary"
}

# ─── Networking ───
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones for multi-AZ deployment"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# ─── Database ───
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Initial storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "selfdiary"
}

variable "db_username" {
  description = "Master database username"
  type        = string
  default     = "selfdiary"
  sensitive   = true
}

# ─── ECS ───
variable "api_cpu" {
  description = "CPU units for API task (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "Memory in MB for API task"
  type        = number
  default     = 512
}

variable "api_desired_count" {
  description = "Desired number of API task replicas"
  type        = number
  default     = 2
}

variable "web_cpu" {
  description = "CPU units for web task"
  type        = number
  default     = 256
}

variable "web_memory" {
  description = "Memory in MB for web task"
  type        = number
  default     = 512
}

variable "web_desired_count" {
  description = "Desired number of web task replicas"
  type        = number
  default     = 2
}

# ─── Container Images ───
variable "api_image" {
  description = "ECR image URI for the API"
  type        = string
}

variable "web_image" {
  description = "ECR image URI for the web app"
  type        = string
}

# ─── Domain ───
variable "domain_name" {
  description = "Base domain name (e.g. selfdiary.example.com)"
  type        = string
  default     = ""
}
