# Step Functions Ingestion Module - Orchestrates document ingestion workflow
# Coordinates Document Processor and Embedding Generator Lambda functions

# Read the state machine definition
locals {
  state_machine_definition = templatefile("${path.module}/state_machine.json", {
    document_processor_lambda_arn  = var.document_processor_lambda_arn
    embedding_generator_lambda_arn = var.embedding_generator_lambda_arn
  })
}

# Create the Step Functions state machine
resource "aws_sfn_state_machine" "ingestion" {
  name       = var.state_machine_name
  role_arn   = var.step_functions_role_arn
  definition = local.state_machine_definition

  tags = {
    Name        = var.state_machine_name
    Environment = var.env
    Project     = var.project_name
  }
}

# EventBridge rule to trigger Step Functions on S3 object creation
resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name        = "${var.env}-${var.project_name}-s3-object-created"
  description = "Trigger Step Functions when documents are uploaded to S3"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [var.s3_bucket_name]
      }
    }
  })

  tags = {
    Name        = "${var.env}-${var.project_name}-s3-object-created"
    Environment = var.env
    Project     = var.project_name
  }
}

# EventBridge target to invoke Step Functions
resource "aws_cloudwatch_event_target" "step_functions" {
  rule      = aws_cloudwatch_event_rule.s3_object_created.name
  target_id = "IngestionStateMachine"
  arn       = aws_sfn_state_machine.ingestion.arn
  role_arn  = var.eventbridge_role_arn

  # Pass the S3 event to Step Functions
  input_transformer = {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }
    input_template = jsonencode({
      detail = {
        bucket = {
          name = "<bucket>"
        }
        object = {
          key = "<key>"
        }
      }
    })
  }
}
