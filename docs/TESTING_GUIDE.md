# End-to-End Testing Guide

This guide walks through testing every component of the ingestion and search pipeline in order.
Run each step, verify the expected output, then move to the next.

---

## Prerequisites

Before starting, get your deployed values from Terraform outputs:

```bash
cd infra
terraform output
```

You will need these values — set them as shell variables:

```bash
export API=https://<your-api-id>.execute-api.us-east-1.amazonaws.com
export BUCKET=dev-opensearch-navco-search-documents-bucket
export STATE_MACHINE_ARN=arn:aws:states:us-east-1:<account-id>:stateMachine:dev-opensearch-navco-search-ingestion
export KB_ID=<knowledge_base_id from terraform output>
export REGION=us-east-1
```

---

## Step 1 — Verify OpenSearch Indexes Exist

Go to AWS Console → Amazon OpenSearch Service → Serverless → Collections → `dev-navco-search` → Indexes tab.

You should see three indexes:
- `metadata-index`
- `vector-index`
- `suggestions-index`

If any are missing, invoke the bootstrap Lambda manually:

```bash
aws lambda invoke \
  --function-name dev-opensearch-navco-search-index-bootstrap \
  --region $REGION \
  /tmp/bootstrap_response.json

cat /tmp/bootstrap_response.json
```

Expected response:
```json
{"statusCode": 200, "body": "{\"message\": \"Indexes created successfully\", \"indexes\": [\"metadata-index\", \"vector-index\", \"suggestions-index\"]}"}
```

---

## Step 2 — Upload a Test Document to S3

Create a sample JSON file that represents a document:

```bash
cat > /tmp/test-document.json << 'EOF'
{
  "document_id": "doc-001",
  "title": "Introduction to Machine Learning",
  "content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
  "category": "Technology",
  "author": "John Smith",
  "tags": ["machine learning", "AI", "data science"],
  "upload_date": "2024-01-15"
}
EOF
```

Upload it to S3:

```bash
aws s3 cp /tmp/test-document.json s3://$BUCKET/test-document.json
```

Expected: upload succeeds with no error.

---

## Step 3 — Trigger the Ingestion Pipeline (Step Functions)

Start the Step Functions state machine manually with the S3 event payload:

```bash
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --region $REGION \
  --input '{
    "bucket": "'$BUCKET'",
    "key": "test-document.json"
  }' \
  --query 'executionArn' \
  --output text
```

Copy the returned execution ARN, then check its status:

```bash
aws stepfunctions describe-execution \
  --execution-arn <execution-arn-from-above> \
  --region $REGION \
  --query 'status' \
  --output text
```

Expected: `SUCCEEDED`

If it shows `FAILED`, get the error detail:

```bash
aws stepfunctions get-execution-history \
  --execution-arn <execution-arn> \
  --region $REGION \
  --query 'events[?type==`TaskFailed`]'
```

---

## Step 4 — Verify Indexer Lambda Indexed the Document

Check the indexer Lambda logs to confirm it processed the file:

```bash
aws logs tail /aws/lambda/dev-opensearch-navco-search-indexer \
  --region $REGION \
  --since 10m
```

Look for log lines like:
```
Loaded JSON from s3://dev-opensearch-navco-search-documents-bucket/test-document.json
Document ID: doc-001
Indexed metadata for doc-001 (10 fields)
Indexed 15 suggestions for doc-001
```

---

## Step 5 — Test the Search API

Test that the document is searchable via the API:

```bash
curl -s "$API/search?query=machine+learning" | python3 -m json.tool
```

Expected response shape:
```json
{
  "query": "machine learning",
  "results": [
    {
      "id": "doc-001",
      "score": 1.5,
      "source": {
        "title": "Introduction to Machine Learning",
        "content": "Machine learning is a subset...",
        "category": "Technology"
      }
    }
  ],
  "count": 1
}
```

Try a few more queries to confirm relevance:

```bash
curl -s "$API/search?query=artificial+intelligence" | python3 -m json.tool
curl -s "$API/search?query=data+science" | python3 -m json.tool
```

Test the 400 error case (missing query):

```bash
curl -s "$API/search" | python3 -m json.tool
# Expected: {"error": "Missing query parameter"}
```

---

## Step 6 — Test the Suggestions API

Test autocomplete suggestions:

```bash
curl -s "$API/suggestions?prefix=mach" | python3 -m json.tool
```

Expected response shape:
```json
{
  "prefix": "mach",
  "suggestions": [
    {"suggestion": "machine learning", "weight": 15, "score": 1.0},
    {"suggestion": "machine", "weight": 10, "score": 0.8}
  ],
  "count": 2
}
```

Try other prefixes from your test document:

```bash
curl -s "$API/suggestions?prefix=art" | python3 -m json.tool
curl -s "$API/suggestions?prefix=data" | python3 -m json.tool
```

Test the 400 error case:

```bash
curl -s "$API/suggestions" | python3 -m json.tool
# Expected: {"error": "Missing prefix parameter"}
```

---

## Step 7 — Trigger Bedrock Knowledge Base Sync

The Bedrock KB does not auto-sync — you need to start an ingestion job manually after uploading documents.

```bash
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $(aws bedrock-agent list-data-sources \
    --knowledge-base-id $KB_ID \
    --region $REGION \
    --query 'dataSourceSummaries[0].dataSourceId' \
    --output text) \
  --region $REGION
```

Check the ingestion job status:

```bash
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $KB_ID \
  --region $REGION \
  --query 'ingestionJobSummaries[0].{status:status,started:startedAt}' \
  --output table
```

Wait until status shows `COMPLETE`. This typically takes 1-3 minutes.

---

## Step 8 — Upload Multiple Documents and Verify Batch Ingestion

Upload a second document to confirm the pipeline handles multiple files:

```bash
cat > /tmp/test-document-2.json << 'EOF'
{
  "document_id": "doc-002",
  "title": "Cloud Computing Fundamentals",
  "content": "Cloud computing delivers computing services over the internet including servers, storage, and databases.",
  "category": "Infrastructure",
  "author": "Jane Doe",
  "tags": ["cloud", "AWS", "infrastructure"],
  "upload_date": "2024-02-01"
}
EOF

aws s3 cp /tmp/test-document-2.json s3://$BUCKET/test-document-2.json
```

Trigger ingestion for the second document:

```bash
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --region $REGION \
  --input '{
    "bucket": "'$BUCKET'",
    "key": "test-document-2.json"
  }'
```

Then search across both documents:

```bash
curl -s "$API/search?query=cloud" | python3 -m json.tool
curl -s "$API/search?query=learning" | python3 -m json.tool
```

---

## Step 9 — Check OpenSearch Dashboard (Optional)

1. Go to AWS Console → Amazon OpenSearch Service → Serverless → Collections → `dev-navco-search`
2. Click "OpenSearch Dashboards URL"
3. Log in with your AWS credentials
4. Go to Dev Tools and run:

```
GET metadata-index/_count
GET suggestions-index/_count
GET vector-index/_count
```

Expected: `metadata-index` and `suggestions-index` should show count > 0 after ingestion.

---

## Step 10 — Verify End-to-End with Lambda Logs

Check all Lambda logs together to confirm the full flow worked:

```bash
# Bootstrap
aws logs tail /aws/lambda/dev-opensearch-navco-search-index-bootstrap --region $REGION --since 1h

# Indexer
aws logs tail /aws/lambda/dev-opensearch-navco-search-indexer --region $REGION --since 1h

# Search
aws logs tail /aws/lambda/dev-opensearch-navco-search-search --region $REGION --since 1h

# Suggestions
aws logs tail /aws/lambda/dev-opensearch-navco-search-suggestions --region $REGION --since 1h
```

---

## Quick Smoke Test (All in One)

Once everything is deployed, run this sequence to verify the whole pipeline in under 2 minutes:

```bash
# 1. Upload doc
aws s3 cp /tmp/test-document.json s3://$BUCKET/smoke-test.json

# 2. Trigger ingestion
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --region $REGION \
  --input '{"bucket":"'$BUCKET'","key":"smoke-test.json"}'

# 3. Wait a few seconds
sleep 5

# 4. Search
curl -s "$API/search?query=machine+learning" | python3 -m json.tool

# 5. Suggestions
curl -s "$API/suggestions?prefix=mach" | python3 -m json.tool
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| `statusCode: 503` from bootstrap | OpenSearch endpoint wrong or index creation failed | Check Lambda env var `OPENSEARCH_ENDPOINT`, re-run bootstrap |
| `statusCode: 500` from indexer | Bad JSON in S3 file or missing bucket/key in event | Validate JSON file, check Step Functions input format |
| `statusCode: 400` from search/suggestions | Missing `query` or `prefix` parameter | Add the required query parameter to the URL |
| `statusCode: 502` from search/suggestions | OpenSearch connection failed | Check IAM role permissions, verify collection is active |
| Step Functions `FAILED` | Indexer Lambda threw an exception | Check indexer CloudWatch logs for the specific error |
| Bedrock KB ingestion `FAILED` | vector-index missing or wrong engine | Re-run bootstrap Lambda, then retry KB ingestion job |
