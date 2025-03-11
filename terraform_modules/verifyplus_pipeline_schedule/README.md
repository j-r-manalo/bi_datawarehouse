# VerifyPlus Pipeline Schedule

## Overview
This Terraform configuration sets up an AWS EventBridge Scheduler to trigger a Lambda function for the `verifyplus_pipeline`. It includes:
- A custom EventBridge Scheduler Schedule Group.
- An IAM role and policy for EventBridge Scheduler to invoke the Lambda function.
- An EventBridge Scheduler rule to execute the Lambda function on a defined schedule.
- Lambda permissions to allow invocation by EventBridge Scheduler.

## Usage
To use this module, see the usage in the main `main.tf`.

## Resources
### 1. **EventBridge Scheduler Schedule Group**
Defines a custom schedule group for organizing the scheduler:
```hcl
resource "aws_scheduler_schedule_group" "verifyplus_pipeline_group" {
  name = "invoice-transactions-verifyplus-pipeline"
}
```

### 2. **IAM Role for Scheduler**
Creates an IAM role that EventBridge Scheduler will assume to invoke the Lambda function:
```hcl
resource "aws_iam_role" "verifyplus_scheduler_role" {
  name = "verifyplus-eventbridge-scheduler-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "scheduler.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}
```

### 3. **IAM Policy for Scheduler**
Defines a policy allowing the scheduler to invoke and retrieve details of the Lambda function:
```hcl
resource "aws_iam_policy" "verifyplus_scheduler_policy" {
  name = "verifyplus-eventbridge-scheduler-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["lambda:InvokeFunction", "lambda:GetFunction"],
        Resource = var.verifyplus_pipeline_lambda_arn
      }
    ]
  })
}
```

### 4. **Attach IAM Policy to Role**
Associates the IAM policy with the scheduler role:
```hcl
resource "aws_iam_role_policy_attachment" "verifyplus_scheduler_policy_attach" {
  role       = aws_iam_role.verifyplus_scheduler_role.name
  policy_arn = aws_iam_policy.verifyplus_scheduler_policy.arn
}
```

### 5. **EventBridge Scheduler Schedule**
Defines the EventBridge Scheduler to trigger the Lambda function at a specific cron schedule:
```hcl
resource "aws_scheduler_schedule" "verifyplus_pipeline_schedule" {
  name                         = "${var.verifyplus_pipeline_lambda_name}-schedule"
  group_name                   = aws_scheduler_schedule_group.verifyplus_pipeline_group.name
  description                  = "Schedule to trigger the Lambda function."
  schedule_expression          = var.verifyplus_cron_schedule
  schedule_expression_timezone = "America/New_York"
  
  flexible_time_window {
    mode = "OFF"
  }
  
  target {
    arn      = var.verifyplus_pipeline_lambda_arn
    role_arn = aws_iam_role.verifyplus_scheduler_role.arn

    retry_policy {
      maximum_retry_attempts = 3
    }

    input = jsonencode({
      Scheduled = true,
      Timestamp = "2024-02-18T10:00:00Z"  # Placeholder timestamp
    })
  }
}
```

### 6. **Lambda Permission for EventBridge Scheduler**
Grants EventBridge Scheduler permission to invoke the Lambda function:
```hcl
resource "aws_lambda_permission" "verifyplus_allow_scheduler_event" {
  statement_id  = "AllowEventBridgeSchedulerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.verifyplus_pipeline_lambda_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.verifyplus_pipeline_schedule.arn
}
```

## Variables
The following Terraform variables are defined in variables.tf:
```hcl
variable "verifyplus_pipeline_lambda_arn" {
  description = "ARN of the VerifyPlus pipeline Lambda function"
  type        = string
}

variable "verifyplus_pipeline_lambda_name" {
  description = "Name of the VerifyPlus pipeline Lambda function"
  type        = string
}

variable "verifyplus_cron_schedule" {
  description = "Cron expression defining the schedule"
  type        = string
}
```

## Deployment
1. Ensure that Terraform and AWS CLI are installed and configured.
2. Make sure you are logged into the correct AWS account.
3. Initialize Terraform:
   ```sh
   terraform init
   ```
4. Plan the deployment:
   ```sh
   terraform plan
   ```
5. Apply the changes:
   ```sh
   terraform apply
   ```

## Notes
- The `verifyplus_cron_schedule` variable is set in main.tf.
- The Lambda function must already exist before applying this configuration.
- Ensure the necessary AWS IAM permissions are granted for Terraform execution.

## Cleanup
To remove the resources, run:
```sh
terraform destroy
```
