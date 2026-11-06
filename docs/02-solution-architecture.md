# 2. Solution Architecture

## Components

```mermaid
flowchart TB
    spa["React SPA"]
    cdn["CDN + WAF"]
    subgraph API["Pricing API (FastAPI)"]
        routes["Routes"] --> services["Services"] --> repos["Repositories"]
    end
    worker["Ingestion worker"]
    db[("PostgreSQL")]
    blob[("File storage<br/>raw CSVs")]
    queue[["Job queue"]]
    idp["Company login (OIDC)"]

    spa --> cdn --> routes
    spa -. login .-> idp
    routes -. check token .-> idp
    services -- "save file" --> blob
    services -- "queue job" --> queue --> worker
    worker -- "read file" --> blob
    worker -- "batch upsert" --> db
    repos --> db
```

| Part | Job | In this repo |
|---|---|---|
| React SPA | Upload, upload history, search, edit, change history | `frontend/` |
| Pricing API | REST endpoints, validation, login and roles | `backend/app` |
| Ingestion worker | Reads the CSV, checks each row, saves in batches of 5,000 | `services/ingestion.py` |
| File storage | Keeps every uploaded file | Local disk (S3 or Blob in production) |
| Job queue | Separates upload from processing | FastAPI background tasks (SQS or Service Bus in production) |
| Database | Prices, uploads, history | PostgreSQL, SQLite for tests |

The code is layered as routes, then services, then repositories. Each layer only calls the one below it.

## Upload flow

```mermaid
sequenceDiagram
    actor U as Analyst
    participant API
    participant S as Storage
    participant W as Worker
    participant DB

    U->>API: POST /ingestions (CSV)
    API->>S: Save file, compute SHA-256
    alt Same file uploaded before
        API-->>U: 409
    else New file
        API->>DB: Create job (pending)
        API-->>U: 202 + job id
    end
    W->>S: Read file
    loop Each batch of 5,000 rows
        W->>DB: Upsert valid rows, save row errors
    end
    W->>DB: Mark job completed or failed
    U->>API: Poll job status
```

## Edit flow

```mermaid
sequenceDiagram
    actor U as User
    participant API
    participant DB

    U->>API: PATCH /pricing-records/42 {price, version: 3}
    API->>DB: UPDATE ... WHERE id = 42 AND version = 3
    alt Updated
        API->>DB: Write change history
        API-->>U: 200
    else Someone else changed it
        API-->>U: 409, user reloads latest
    end
```

## Data model

```mermaid
erDiagram
    INGESTION_JOBS ||--o{ INGESTION_ERRORS : has
    INGESTION_JOBS ||--o{ PRICING_RECORDS : loaded
    PRICING_RECORDS ||--o{ PRICING_AUDIT : history

    INGESTION_JOBS {
        string id PK
        string filename
        string checksum
        string status
        int accepted_rows
        int rejected_rows
        string uploaded_by
    }
    INGESTION_ERRORS {
        bigint id PK
        string job_id FK
        int row_number
        string message
    }
    PRICING_RECORDS {
        bigint id PK
        string store_id "unique with sku, date"
        string sku
        date price_date
        string product_name
        decimal price "14,4"
        int version
        string source_job_id FK
    }
    PRICING_AUDIT {
        bigint id PK
        bigint record_id FK
        json changes "old and new values"
        string changed_by
    }
```

Indexes follow the common searches: store + date, SKU + date, date alone, and a trigram index for "product name contains".

## Production deployment

AWS is shown here. Azure has a matching service for each part.

```mermaid
flowchart TB
    users(["Users"]) --> cf["CloudFront + WAF"]
    cf --> s3web[("S3: SPA files")]
    cf -- "/api" --> alb["Load balancer"]
    subgraph Region["Primary region, 3 zones"]
        alb --> api["API tasks (min 3)"]
        api -- "large files direct" --> raw[("S3 raw feeds")]
        raw -- "new file event" --> sqs[["SQS + dead-letter queue"]] --> worker["Workers, scale on queue"]
        api --> aurora[("Aurora PostgreSQL<br/>multi-zone + read replicas")]
        worker --> aurora
    end
    aurora -. replicate .-> dr[("DR region")]
    raw -. replicate .-> dr
```

| | This repo | Production |
|---|---|---|
| Processing | Background task in the API | Separate worker reading from a queue |
| Big files | Sent through the API, up to 512 MB | Uploaded straight to S3 |
| Storage | Local disk | S3 or Blob, same interface |
| Database | One PostgreSQL | Managed PostgreSQL, replicas, monthly partitions |

If some countries require data to stay inside their borders, the same build can run as separate regional deployments, one per region.
