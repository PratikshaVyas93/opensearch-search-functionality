# opensearch-search-functionality
Run terraform validate
/home/runner/work/_temp/10d44870-a81a-4b43-9e18-e722265e6ba3/terraform-bin validate
╷
│ Error: Unsupported argument
│ 
│   on modules/api_gateway/main.tf line 64, in resource "aws_apigatewayv2_integration" "search_lambda":
│   64:   target                 = var.search_lambda_invoke_arn
│ 
│ An argument named "target" is not expected here.
╵
╷
│ Error: Unsupported argument
│ 
│   on modules/api_gateway/main.tf line 87, in resource "aws_apigatewayv2_integration" "suggestions_lambda":
│   87:   target                 = var.suggestions_lambda_invoke_arn
│ 
│ An argument named "target" is not expected here.
╵
╷
│ Error: Invalid resource type
│ 
│   on modules/bedrock_knowledge_base/main.tf line 71, in resource "aws_bedrock_knowledge_base" "this":
│   71: resource "aws_bedrock_knowledge_base" "this" {
│ 
│ The provider hashicorp/aws does not support resource type
│ "aws_bedrock_knowledge_base".
╵
╷
│ Error: Invalid function argument
│ 
│   on modules/step_functions_ingestion/main.tf line 6, in locals:
│    6:   state_machine_definition = templatefile("${path.module}/state_machine.json", {
│    7:     document_processor_lambda_arn  = var.document_processor_lambda_arn
│    8:     embedding_generator_lambda_arn = var.embedding_generator_lambda_arn
│    9:   })
│     ├────────────────
│     │ while calling templatefile(path, vars)
│     │ path.module is "modules/step_functions_ingestion"
│ 
│ Invalid value for "path" parameter: no file exists at
│ "modules/step_functions_ingestion/state_machine.json"; this function works
│ only with files that are distributed as part of the configuration source
│ code, so if this file will be created by a resource in this configuration
│ you must instead obtain this result from an attribute of that resource.
╵
Error: Terraform exited with code 1.
Error: Process completed with exit code 1.
0s
0s
0s
0s
