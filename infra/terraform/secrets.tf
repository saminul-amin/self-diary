# ──────────────────────────────────────────────
# Secrets Manager — Application Secrets
# ──────────────────────────────────────────────

resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.project_name}/${var.environment}/app"
  description             = "Application secrets for ${var.project_name} ${var.environment}"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
}

# Initial secret values — update via AWS Console or CLI after first deploy.
# The placeholder values MUST be replaced before running the application.
resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    DATABASE_URL   = "postgresql+asyncpg://${var.db_username}:REPLACE_ME@${aws_db_instance.main.endpoint}/${var.db_name}"
    JWT_SECRET_KEY = "REPLACE_ME_WITH_SECURE_RANDOM_KEY"
    S3_ACCESS_KEY  = "REPLACE_ME"
    S3_SECRET_KEY  = "REPLACE_ME"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
