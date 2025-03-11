#############################
# Custom Schedule Group
#############################
resource "aws_scheduler_schedule_group" "demand_pipeline_group" {
  name = "invoice-transactions-demand-pipeline"
}

#############################
# Custom Scheduler Role
#############################
resource "aws_iam_role" "scheduler_role" {
  name = "eventbridge-scheduler-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "scheduler.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "scheduler_policy" {
  name = "eventbridge-scheduler-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "lambda:InvokeFunction",
          "lambda:GetFunction"
        ],
        Resource = var.demand_pipeline_lambda_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "scheduler_policy_attach" {
  role       = aws_iam_role.scheduler_role.name
  policy_arn = aws_iam_policy.scheduler_policy.arn
}

#############################
# EventBridge Scheduler Schedule for Lambda
#############################
resource "aws_scheduler_schedule" "demand_pipeline_schedule" {
  name                         = "${var.demand_pipeline_lambda_name}-schedule"
  group_name                   = aws_scheduler_schedule_group.demand_pipeline_group.name
  description                  = "Schedule to trigger the Lambda function."
  schedule_expression          = var.cron_schedule
  schedule_expression_timezone = "America/New_York"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = var.demand_pipeline_lambda_arn
    role_arn = aws_iam_role.scheduler_role.arn

    retry_policy {
      maximum_retry_attempts = 3
    }

    # Simplified input structure
    input = jsonencode({
      Scheduled = true,
      Timestamp = "2024-02-18T10:00:00Z"  # Will be replaced by actual time
    })
  }
}

#############################
# Allow EventBridge Scheduler to invoke Lambda
#############################
resource "aws_lambda_permission" "allow_scheduler_event" {
  statement_id  = "AllowEventBridgeSchedulerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.demand_pipeline_lambda_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.demand_pipeline_schedule.arn
}