variable "collection_name" {
  type        = string
  description = "Name of the OpenSearch Serverless collection"
}

variable "access_principal_arns" {
  type        = list(string)
  description = "List of IAM principal ARNs that will be granted full access to the collection and its indexes"
}
