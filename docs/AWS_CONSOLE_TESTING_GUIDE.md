# AWS Console Testing Guide — Complete Pipeline

This guide walks through testing the entire ingestion and search pipeline using only the AWS Console (no CLI commands).

---

## Prerequisites

Before starting, you need these values from your Terraform deployment. Get them from:
1. Go to **AWS Console** → **CloudFormation** (or search for your stack)
2. Find your stack → **Outputs** tab
3. Note down:
   - `api_endpoint` (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com`)
   - `search_endpoint` (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/search`)
   - `suggestions_endpoint` (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/suggestions`)
   - `s3_bucket_name` (e.g., `dev-opensearch-navco-search-documents-bucket`)
   - `state_machine_arn` (e.g., `arn:aws:states:us-east-1:123456789012:stateMachine:dev-opensearch-navco-search-ingestion`)
   - `knowledge_base_id` (e.g., `ABCDEF1234`)

---

## Step 1 — Verify OpenSearch Indexes Exist

**Goal:** Confirm the three required indexes were created by the bootstrap Lambda.

### In AWS Console:

1. Search for **"OpenSearch"** in the search bar
2. Click **"Amazon OpenSearch Service"**
3. In the left sidebar, click **"Serverless"** → **"Collections"**
4. Click on your collection named **`dev-navco-search`**
5. Click the **"Indexes"** tab

**Expected:** You should see three indexes:
- `metadata-index`
- `vector-index`
- `suggestions-index`

**If indexes are missing:**
1. Go to **Lambda** (search for it)
2. Find the function named **`dev-opensearch-navco-search-index-bootstrap`**
3. Click it
4. Click the **"Test"** button (top right)
5. In the test event, paste:
   ```json
   {}
   ```
6. Click **"Test"** again
7. Wait for execution to complete
8. Check the **"Response"** section — should show `statusCode: 200`
9. Go back to OpenSearch Indexes tab and refresh — indexes should now appear

---

## Step 2 — Create a Test Document

**Goal:** Create a sample JSON document to upload to S3.

### In AWS Console:

1. Open **Notepad** or any text editor on your computer
2. Paste this content:

```json
{
  "document_id": "doc-001",
  "title": "Introduction to Machine Learning",
  "content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data without being explicitly programmed.",
  "category": "Technology",
  "author": "John Smith",
  "tags": ["machine learning", "AI", "data science"],
  "upload_date": "2024-01-15"
}
```

3. Save the file as **`test-document.json`** on your computer

---

## Step 3 — Upload Document to S3

**Goal:** Upload the test document to the S3 bucket so the ingestion pipeline can process it.

### In AWS Console:

1. Search for **"S3"** in the search bar
2. Click **"S3"** (Simple Storage Service)
3. In the bucket list, find and click the bucket named **`dev-opensearch-navco-search-documents-bucket`**
4. Click the **"Upload"** button (top left)
5. Click **"Add files"**
6. Select the **`test-document.json`** file you created in Step 2
7. Click **"Upload"** button at the bottom
8. Wait for the upload to complete (you'll see a green checkmark)

**Expected:** File appears in the bucket with size shown (should be ~300 bytes).

---

## Step 4 — Trigger the Ingestion Pipeline

**Goal:** Start the Step Functions state machine to process the uploaded document.

### In AWS Console:

1. Search for **"Step Functions"** in the search bar
2. Click **"Step Functions"**
3. In the left sidebar, click **"State machines"**
4. Find and click the state machine named **`dev-opensearch-navco-search-ingestion`**
5. Click the **"Start execution"** button (top right)
6. In the **"Input"** field, paste:

```json
{
  "bucket": "dev-opensearch-navco-search-documents-bucket",
  "key": "test-document.json"
}
```

7. Click **"Start execution"** button
8. You'll see a new execution appear with a unique ID

**Expected:** Execution status shows **`RUNNING`** initially, then changes to **`SUCCEEDED`** within 10 seconds.

**If status shows `FAILED`:**
1. Click on the failed execution
2. Scroll down to the **"Execution events"** section
3. Look for the red **"TaskFailed"** event
4. Click it to see the error details
5. Check Step 5 (Lambda logs) for more information

---

## Step 5 — Verify Indexer Lambda Processed the Document

**Goal:** Confirm the indexer Lambda successfully indexed the document into OpenSearch.

### In AWS Console:

1. Search for **"Lambda"** in the search bar
2. Click **"Lambda"**
3. In the left sidebar, click **"Functions"**
4. Find and click the function named **`dev-opensearch-navco-search-indexer`**
5. Click the **"Monitor"** tab
6. Click **"View logs in CloudWatch"** (on the right)
7. You'll see a list of log streams — click the most recent one (top of the list)
8. Scroll down to find log lines like:

```
Loaded JSON from s3://dev-opensearch-navco-search-documents-bucket/test-document.json
Document ID: doc-001
Indexed metadata for doc-001 (10 fields)
Indexed 15 suggestions for doc-001
```

**Expected:** You should see these log lines confirming the document was indexed.

**If you don't see these logs:**
1. Go back to the Lambda function
2. Click the **"Test"** button
3. Paste this test event:
   ```json
   {
     "detail": {
       "bucket": {
         "name": "dev-opensearch-navco-search-documents-bucket"
       },
       "object": {
         "key": "test-document.json"
       }
     }
   }
   ```
4. Click **"Test"** again
5. Check the response — should show `statusCode: 200`
6. Go back to CloudWatch logs and refresh

---

## Step 6 — Test the Search API

**Goal:** Verify the document is searchable through the API.

### In AWS Console:

1. Open a new browser tab
2. In the address bar, paste this URL (replace `<api_endpoint>` with your actual endpoint from Prerequisites):

```
<api_endpoint>/search?query=machine+learning
```

**Example:**
```
https://abc123.execute-api.us-east-1.amazonaws.com/search?query=machine+learning
```

3. Press **Enter**
4. You should see a JSON response like:

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

**Try these other searches:**

- `<api_endpoint>/search?query=artificial+intelligence`
- `<api_endpoint>/search?query=data+science`
- `<api_endpoint>/search?query=programming`

**Test error case (missing query parameter):**

- `<api_endpoint>/search`

Expected response:
```json
{"error": "Missing query parameter"}
```

---

## Step 7 — Test the Suggestions API

**Goal:** Verify autocomplete suggestions work.

### In AWS Console:

1. Open a new browser tab
2. In the address bar, paste this URL (replace `<suggestions_endpoint>`):

```
<suggestions_endpoint>?prefix=mach
```

**Example:**
```
https://abc123.execute-api.us-east-1.amazonaws.com/suggestions?prefix=mach
```

3. Press **Enter**
4. You should see a JSON response like:

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

**Try these other prefixes:**

- `<suggestions_endpoint>?prefix=art` (should suggest "artificial intelligence")
- `<suggestions_endpoint>?prefix=data` (should suggest "data science")
- `<suggestions_endpoint>?prefix=tech` (should suggest "Technology")

**Test error case:**

- `<suggestions_endpoint>` (without prefix parameter)

Expected response:
```json
{"error": "Missing prefix parameter"}
```

---

## Step 8 — Check OpenSearch Dashboard

**Goal:** View the indexed data directly in OpenSearch Dashboards.

### In AWS Console:

1. Search for **"OpenSearch"** in the search bar
2. Click **"Amazon OpenSearch Service"**
3. Click **"Serverless"** → **"Collections"**
4. Click on **`dev-navco-search`**
5. Scroll down to find the **"OpenSearch Dashboards URL"** link
6. Click it (opens in a new tab)
7. Log in with your AWS credentials
8. Click **"Dev Tools"** (left sidebar)
9. In the console, run these queries one by one:

**Query 1 — Count metadata documents:**
```
GET metadata-index/_count
```

Expected response:
```json
{"count": 1, "_shards": {...}}
```

**Query 2 — Count suggestions:**
```
GET suggestions-index/_count
```

Expected response:
```json
{"count": 15, "_shards": {...}}
```

**Query 3 — View all metadata:**
```
GET metadata-index/_search
```

Expected response shows your document with all fields.

---

## Step 9 — Trigger Bedrock Knowledge Base Sync

**Goal:** Sync the indexed documents to Bedrock Knowledge Base for RAG queries.

### In AWS Console:

1. Search for **"Bedrock"** in the search bar
2. Click **"Amazon Bedrock"**
3. In the left sidebar, click **"Knowledge bases"**
4. Find and click your knowledge base (name like `dev-opensearch-navco-search-kb`)
5. Click the **"Data sources"** tab
6. You should see one data source (S3 bucket)
7. Click the **"Sync"** button (top right)
8. A dialog appears — click **"Sync"** to confirm
9. Wait for the sync to complete (status changes from `SYNCING` to `READY`)

**Expected:** Status shows `READY` within 1-3 minutes.

**If sync fails:**
1. Click on the data source
2. Check the **"Sync history"** tab for error details
3. Common issues:
   - Vector index has wrong engine (should be `faiss`) — re-run bootstrap Lambda
   - S3 bucket permissions — check IAM role

---

## Step 10 — Upload a Second Document and Test Batch Processing

**Goal:** Verify the pipeline handles multiple documents.

### In AWS Console:

1. Open **Notepad** again
2. Paste this content:

```json
{
  "document_id": "doc-002",
  "title": "Cloud Computing Fundamentals",
  "content": "Cloud computing delivers computing services over the internet including servers, storage, and databases. It enables scalable and flexible infrastructure.",
  "category": "Infrastructure",
  "author": "Jane Doe",
  "tags": ["cloud", "AWS", "infrastructure"],
  "upload_date": "2024-02-01"
}
```

3. Save as **`test-document-2.json`**
4. Go to **S3** → your bucket
5. Click **"Upload"** → **"Add files"** → select the new file
6. Click **"Upload"**
7. Go to **Step Functions** → your state machine
8. Click **"Start execution"**
9. Paste this input:

```json
{
  "bucket": "dev-opensearch-navco-search-documents-bucket",
  "key": "test-document-2.json"
}
```

10. Click **"Start execution"**
11. Wait for it to complete (status = `SUCCEEDED`)

### Now test searches across both documents:

1. Open browser tab with search API
2. Try these queries:
   - `<api_endpoint>/search?query=cloud`
   - `<api_endpoint>/search?query=learning`
   - `<api_endpoint>/search?query=infrastructure`

**Expected:** Results should include both documents where relevant.

---

## Step 11 — Monitor Lambda Performance

**Goal:** Check Lambda execution times and error rates.

### In AWS Console:

1. Search for **"Lambda"** in the search bar
2. Click **"Lambda"**
3. Click **"Functions"**
4. For each function, click it and check the **"Monitor"** tab:
   - `dev-opensearch-navco-search-index-bootstrap`
   - `dev-opensearch-navco-search-indexer`
   - `dev-opensearch-navco-search-search`
   - `dev-opensearch-navco-search-suggestions`

**Check these metrics:**
- **Invocations** — should match number of times you called it
- **Duration** — should be < 5 seconds for most functions
- **Errors** — should be 0 (or show specific errors if any)
- **Throttles** — should be 0

**If you see errors:**
1. Click **"View logs in CloudWatch"**
2. Click the most recent log stream
3. Scroll to find the error message
4. Common errors and fixes are in the troubleshooting section below

---

## Step 12 — Full End-to-End Verification

**Goal:** Confirm the entire pipeline works from upload to search.

### Checklist:

- [ ] OpenSearch indexes exist (Step 1)
- [ ] Document uploaded to S3 (Step 3)
- [ ] Step Functions execution succeeded (Step 4)
- [ ] Indexer Lambda logs show document was indexed (Step 5)
- [ ] Search API returns the document (Step 6)
- [ ] Suggestions API returns suggestions (Step 7)
- [ ] OpenSearch Dashboard shows indexed data (Step 8)
- [ ] Bedrock KB sync completed (Step 9)
- [ ] Second document ingested and searchable (Step 10)
- [ ] Lambda metrics show no errors (Step 11)

**If all checkboxes are checked:** Your pipeline is working correctly!

---

## Troubleshooting

### Problem: OpenSearch Indexes Don't Exist

**Solution:**
1. Go to **Lambda** → `dev-opensearch-navco-search-index-bootstrap`
2. Click **"Test"**
3. Paste: `{}`
4. Click **"Test"**
5. Wait for completion
6. Go back to OpenSearch and refresh

---

### Problem: Step Functions Execution Failed

**Solution:**
1. Click on the failed execution
2. Scroll to **"Execution events"**
3. Find the red **"TaskFailed"** event
4. Click it to see error details
5. Common errors:
   - **"No such index"** → Run bootstrap Lambda (see above)
   - **"Access Denied"** → Check IAM role permissions
   - **"Invalid JSON"** → Check the JSON file format

---

### Problem: Search API Returns Empty Results

**Solution:**
1. Verify document was indexed:
   - Go to **Lambda** → `dev-opensearch-navco-search-indexer`
   - Click **"Monitor"** → **"View logs in CloudWatch"**
   - Check for "Indexed metadata" log line
2. If logs show indexing succeeded but search returns nothing:
   - Go to **OpenSearch Dashboard** → **"Dev Tools"**
   - Run: `GET metadata-index/_search`
   - If this returns 0 results, the indexing failed silently
   - Re-run the indexer Lambda with the test event

---

### Problem: Suggestions API Returns Empty Results

**Solution:**
1. Same as search API above
2. Also check: `GET suggestions-index/_count` in OpenSearch Dashboard
3. Should show count > 0 after indexing

---

### Problem: Bedrock KB Sync Failed

**Solution:**
1. Go to **Bedrock** → **"Knowledge bases"** → your KB
2. Click **"Data sources"** tab
3. Click on the data source
4. Check **"Sync history"** for error details
5. Common errors:
   - **"Vector index engine is invalid"** → Vector index has wrong engine
     - Go to **Lambda** → `dev-opensearch-navco-search-index-bootstrap`
     - Click **"Test"** → paste `{}` → click **"Test"**
     - Wait for completion
     - Retry KB sync
   - **"No such index"** → Indexes don't exist
     - Run bootstrap Lambda (see above)

---

### Problem: Lambda Timeout

**Solution:**
1. Go to **Lambda** → the function that timed out
2. Click **"Configuration"** tab
3. Click **"General configuration"** → **"Edit"**
4. Increase **"Timeout"** from 30 to 60 seconds
5. Click **"Save"**
6. Retry the operation

---

## Quick Reference — API Endpoints

| Operation | URL | Example |
|---|---|---|
| Search | `<api_endpoint>/search?query=<term>` | `https://abc123.../search?query=machine+learning` |
| Suggestions | `<suggestions_endpoint>?prefix=<prefix>` | `https://abc123.../suggestions?prefix=mach` |

---

## Next Steps

Once the pipeline is working:

1. **Upload real documents** — Replace test documents with your actual data
2. **Test with Bedrock Agent** — Use the KB ID to query via Bedrock Agent API
3. **Monitor costs** — Check CloudWatch for Lambda invocations and OpenSearch usage
4. **Set up automation** — Configure S3 event notifications to auto-trigger ingestion
5. **Scale up** — Increase Lambda memory/timeout if processing large documents

