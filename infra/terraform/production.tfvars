# Production environment
environment = "production"
aws_region  = "us-east-1"

# Database — larger for production
db_instance_class    = "db.t4g.small"
db_allocated_storage = 50
db_name              = "selfdiary_production"
db_username          = "selfdiary"

# ECS — higher availability for production
api_cpu           = 512
api_memory        = 1024
api_desired_count = 2

web_cpu           = 256
web_memory        = 512
web_desired_count = 2

# Images — overridden by CI/CD
api_image = "selfdiary-api:latest"
web_image = "selfdiary-web:latest"

# Domain
domain_name = ""
