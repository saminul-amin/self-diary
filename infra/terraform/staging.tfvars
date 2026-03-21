# Staging environment
environment = "staging"
aws_region  = "us-east-1"

# Database — smaller for staging
db_instance_class    = "db.t4g.micro"
db_allocated_storage = 20
db_name              = "selfdiary_staging"
db_username          = "selfdiary"

# ECS — minimal for staging
api_cpu           = 256
api_memory        = 512
api_desired_count = 1

web_cpu           = 256
web_memory        = 512
web_desired_count = 1

# Images — overridden by CI/CD
api_image = "selfdiary-api:latest"
web_image = "selfdiary-web:latest"
