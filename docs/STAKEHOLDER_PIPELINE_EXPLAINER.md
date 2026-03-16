# Document Search Platform — How It Works
### For Stakeholders and Technical Team

---

## The Big Picture

This platform does two things:

1. **Ingests documents** — when a file is uploaded, the system automatically processes it and makes it searchable
2. **Serves search** — when a user types a query or prefix, the system returns ranked results or autocomplete suggestions

---

## FLOW 1: Document Ingestion Pipeline

> "A document is uploaded — how does it become searchable?"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DOCUMENT INGESTION PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────────┘

  UPLOAD
  ──────
  User/System uploads a single JSON file to S3.
  The JSON can have ANY fields — no fixed schema required.

  Examples of valid uploads:

  File 1: { "title": "Q3 Report", "author": "Finance", "content": "..." }
  File 2: { "product_name": "Widget A", "sku": "W-001", "description": "..." }
  File 3: { "case_id": "C-123", "summary": "...", "priority": "high" }

  All are handled identically — every field is indexed dynamically.

                            │
                            ▼
  ┌─────────────────────────────────────┐
  │           Amazon S3 Bucket          │
  │   dev-opensearch-navco-search-      │
  │         documents-bucket            │
  │                                     │
  │  Accepts: any .json file            │
  │  Many files can be uploaded —       │
  │  each triggers its own pipeline     │
  └──────────────┬──────────────────────┘
                 │  S3 ObjectCreated event fires automatically
                 ▼
  ┌─────────────────────────────────────┐
  │           Amazon EventBridge        │
  │   Watches S3 for new file uploads   │
  │   Passes: bucket name + file key    │
  └──────────────┬──────────────────────┘
                 │  Triggers ingestion workflow
                 ▼
  ┌─────────────────────────────────────┐
  │        AWS Step Functions           │
  │      Ingestion Orchestrator         │
  │                                     │
  │  Runs two jobs IN PARALLEL:         │
  │  ┌─────────────┐ ┌───────────────┐  │
  │  │   Job 1     │ │    Job 2      │  │
  │  │  Bedrock KB │ │  Indexer      │  │
  │  └──────┬──────┘ └──────┬────────┘  │
  └─────────┼───────────────┼───────────┘
            │               │
            ▼               ▼

  ┌──────────────────┐   ┌──────────────────────────────────┐
  │  Bedrock         │   │  Metadata/Suggestions            │
  │  Knowledge Base  │   │  Indexer Lambda                  │
  │  (Titan Embed)   │   │  (src/indexer/index.py)          │
  │                  │   │                                  │
  │  What it does:   │   │  What it does:                   │
  │  • Reads the     │   │  • Downloads the same JSON       │
  │    raw file      │   │    file from S3                  │
  │  • Splits into   │   │  • Reads ALL fields dynamically  │
  │    chunks        │   │    — no fixed schema needed      │
  │  • Converts each │   │  • Stores every field into       │
  │    chunk to a    │   │    metadata-index as-is          │
  │    1536-dim      │   │  • Extracts all string/list      │
  │    vector        │   │    values as suggestions         │
  │  • Writes to     │   │    (full phrases + tokens)       │
  │    chunk-index   │   │  • Works for ANY JSON shape —    │
  │                  │   │    each file can have completely  │
  │  AWS manages:    │   │    different fields              │
  │  everything      │   └──────────────┬───────────────────┘
  │  └──────────┬───────┘                  │
             │                          │
             └──────────┬───────────────┘
                        │  Both write to
                        ▼
  ┌─────────────────────────────────────────────────────┐
  │           OpenSearch Serverless Collection          │
  │                 dev-navco-search                    │
  │                                                     │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
  │  │ chunk-index │  │metadata-    │  │suggestions- │ │
  │  │             │  │index        │  │index        │ │
  │  │ text chunks │  │             │  │             │ │
  │  │ + vectors   │  │ ALL fields  │  │ phrases +   │ │
  │  │             │  │ from JSON   │  │ tokens from │ │
  │  │ Written by: │  │ stored      │  │ all string  │ │
  │  │ Bedrock KB  │  │ dynamically │  │ fields      │ │
  │  │             │  │             │  │             │ │
  │  │             │  │ Written by: │  │ Written by: │ │
  │  │             │  │ Indexer     │  │ Indexer     │ │
  │  │             │  │ Lambda      │  │ Lambda      │ │
  │  └─────────────┘  └─────────────┘  └─────────────┘ │
  └─────────────────────────────────────────────────────┘

  Document is now fully searchable.
```

---

## FLOW 2: Search Pipeline

> "A user types a query — how do they get results?"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SEARCH PIPELINE                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  User types: "quarterly revenue report"
        │
        ▼
  ┌─────────────────────────────────────┐
  │           API Gateway               │
  │   dev-opensearch-navco-search-api   │
  │                                     │
  │   POST /search                      │
  │   GET  /suggestions                 │
  └──────────────┬──────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
  ┌───────────┐     ┌───────────────┐
  │  /search  │     │ /suggestions  │
  │  Lambda   │     │   Lambda      │
  └─────┬─────┘     └──────┬────────┘
        │                  │
        ▼                  ▼

  Hybrid Query:              Prefix Query:
  Searches BOTH              "quart" →
  chunk-index                returns
  + metadata-index           ["quarterly",
  Returns ranked             "quarterly report",
  document results           "quarter end"]
        │                         │
        └──────────┬──────────────┘
                   │  Both query
                   ▼
  ┌─────────────────────────────────────────────────────┐
  │           OpenSearch Serverless Collection          │
  │                                                     │
  │  Search Lambda runs:                                │
  │  • multi_match on metadata-index (title, content)  │
  │  • knn_vector on chunk-index (semantic similarity) │
  │  • Combines + deduplicates results                  │
  │                                                     │
  │  Suggestions Lambda runs:                           │
  │  • match_phrase_prefix on suggestions-index        │
  │  • Sorted by weight (most relevant first)          │
  └──────────────────────┬──────────────────────────────┘
                         │
                         ▼
                   JSON response
                   back to user
```

---

## End-to-End Summary (One Page)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   INGEST                          STORE                    SEARCH           │
│   ──────                          ─────                    ──────           │
│                                                                             │
│   Upload file ──► S3              OpenSearch               API Gateway      │
│        │           │              Serverless               /search          │
│        │           │ ObjectCreated    │                    /suggestions     │
│        │           ▼              ┌──┴──────────┐              │           │
│        │      EventBridge         │ chunk-index │◄─────────────┤           │
│        │           │              │ (vectors)   │         Search Lambda     │
│        │           ▼              ├─────────────┤              │           │
│        │     Step Functions       │metadata-    │◄─────────────┤           │
│        │      Orchestrator        │index        │         Suggestions       │
│        │      ┌────┴────┐         ├─────────────┤         Lambda            │
│        │      │         │         │suggestions- │                           │
│        │      ▼         ▼         │index        │                           │
│        │  Bedrock   Indexer       └─────────────┘                           │
│        │    KB      Lambda                                                  │
│        │  (chunks   (metadata                                               │
│        └──► +        + suggest.)                                            │
│           vectors)                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Who Does What — Responsibility Table

| Component | Owned By | Responsibility |
|---|---|---|
| S3 Bucket | AWS (managed) | Stores raw documents and sidecar metadata files |
| EventBridge | AWS (managed) | Detects new uploads, fires trigger automatically |
| Step Functions | AWS (managed) | Orchestrates the two ingestion jobs, handles failures |
| Bedrock Knowledge Base | AWS (managed) | Reads file, chunks it, embeds each chunk with Titan, writes vectors |
| Indexer Lambda | Your code | Reads sidecar JSON, writes metadata + suggestions to OpenSearch |
| OpenSearch Serverless | AWS (managed) | Stores and searches all three indexes |
| API Gateway | AWS (managed) | Public HTTPS endpoints, routes to correct Lambda |
| Search Lambda | Your code | Runs hybrid query, returns ranked results |
| Suggestions Lambda | Your code | Runs prefix query, returns autocomplete list |

---

## Key Points for Stakeholders

**Why Bedrock Knowledge Base instead of custom embedding code?**
AWS manages the entire chunking and embedding pipeline. No code to maintain, automatic updates, built-in retry logic, and it scales to any document size automatically.

**Why still have an Indexer Lambda?**
Bedrock KB only handles the vector/semantic side. Your business metadata and autocomplete suggestions need custom logic — that's what the Indexer Lambda does. It reads the same JSON file you uploaded, stores every field dynamically into the metadata index, and extracts all string values as autocomplete suggestions. No schema changes needed when your JSON structure changes.

**What JSON format is expected?**
Any valid JSON file works. There is no fixed schema. Each file can have completely different fields — the indexer reads whatever is there and stores it all. The document ID is taken from a `document_id` or `id` field if present, otherwise the S3 key is used. Suggestions are automatically extracted from all string and list fields.

**Why three separate OpenSearch indexes?**
Each index is optimised for a different query type. The chunk index uses k-NN vector search for semantic similarity. The metadata index uses full-text search for keyword matching. The suggestions index uses prefix matching for autocomplete. Combining them gives users both precise keyword results and semantically related results.

**What happens if ingestion fails?**
Step Functions captures the failure, marks the execution as failed, and you can see exactly which step failed and why in the AWS Console. You can re-run just the failed execution without re-uploading the document.

**How do documents get uploaded?**
Upload any JSON file directly to the S3 documents bucket. Each upload automatically triggers the full ingestion pipeline — Bedrock KB for vector indexing and the Indexer Lambda for metadata and suggestions. Multiple files can be uploaded at any time, each runs its own independent pipeline execution.
