# IAM role for EventBridge to invoke Step Functions
resource "aws_iam_role" "eventbridge_role" {
  name = "${var.rule_name}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM policy for EventBridge to invoke Step Functions
resource "aws_iam_role_policy" "eventbridge_invoke_sfn" {
  name = "${var.rule_name}-eventbridge-invoke-sfn"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = aws_sfn_state_machine.ingestion.arn
      }
    ]
  })
}

# IAM role for Step Functions to invoke Lambda
resource "aws_iam_role" "step_functions_role" {
  name = "${var.state_machine_name}-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM policy for Step Functions to invoke Lambda
resource "aws_iam_role_policy" "step_functions_invoke_lambda" {
  name = "${var.state_machine_name}-step-functions-invoke-lambda"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = var.indexer_lambda_arn
      }
    ]
  })
}

# Step Functions state machine for ingestion pipeline
resource "aws_sfn_state_machine" "ingestion" {
  name       = var.state_machine_name
  role_arn   = aws_iam_role.step_functions_role.arn
  definition = jsonencode({
    Comment = "Ingestion pipeline - index document metadata and suggestions"
    StartAt = "InvokeIndexer"
    States = {
      InvokeIndexer = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          "FunctionName.$" = "$.Execution.Input.indexer_function_name"
          "Payload.$"      = "$"
        }
        End = true
      }
    }
  })
}

# EventBridge rule for S3 ObjectCreated events
resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name        = var.rule_name
  description = "Trigger Step Functions state machine on S3 ObjectCreated events"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [data.aws_s3_bucket.source.id]
      }
    }
  })
}

# EventBridge target to invoke Step Functions state machine
resource "aws_cloudwatch_event_target" "invoke_state_machine" {
  rule      = aws_cloudwatch_event_rule.s3_object_created.name
  target_id = "InvokeIngestionStateMachine"
  arn       = aws_sfn_state_machine.ingestion.arn
  role_arn  = aws_iam_role.eventbridge_role.arn

  input_transformer = {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }
    input_template = jsonencode({
      Execution = {
        Input = {
          indexer_function_name = var.indexer_lambda_arn
          bucket                = "<bucket>"
          key                   = "<key>"
        }
      }
    })
  }
}

# Data source to get S3 bucket name from ARN
data "aws_s3_bucket" "source" {
  bucket = split(":::", split(":", var.s3_bucket_arn)[5])[0]
}
