output "itc_data_warehouse_resources" {
  value = {
    database_endpoint              = aws_db_instance.itc_postgres_instance.endpoint
    database_identifier            = var.db_identifier
    database_secret_arn            = aws_secretsmanager_secret.itc_database_secret.arn
    database_secret_name           = var.secret_name
    database_subnet_group_name     = aws_db_subnet_group.itc_db_subnet_group.name
    database_connect_arn           = "arn:aws:rds-db:${local.region}:${local.aws_account_id}:dbuser:*/postgres"
    shared_lambda_sg_id            = aws_security_group.shared_lambda_sg.id
  }
  description = "A map of key resources for the ITC data warehouse."
}