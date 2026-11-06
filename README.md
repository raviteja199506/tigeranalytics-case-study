# Pricing Feed Manager

A single-page web application for a retail chain of 3,000 stores across several countries. It lets users:

- **upload and store pricing feeds** from stores as CSV files (`Store ID, SKU, Product Name, Price, Date`)
- **search pricing records** by store, SKU, product name, price range and date range
- **edit and save** any record, with concurrency protection and a full change history

**Stack:** React 18 + TypeScript + TanStack Query (Vite) · Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic · PostgreSQL 16

## Deliverables

| Deliverable | Location |
|---|---|
| Context diagram | [docs/01-context-diagram.md](docs/01-context-diagram.md) |
| Solution architecture (logical, flows, data model, deployment) | [docs/02-solution-architecture.md](docs/02-solution-architecture.md) |
| Design decisions | [docs/03-design-decisions.md](docs/03-design-decisions.md) |
| Non-functional requirements and how they are addressed | [docs/04-non-functional-requirements.md](docs/04-non-functional-requirements.md) |
| Assumptions | [docs/05-assumptions.md](docs/05-assumptions.md) |
| Source code | [backend/](backend/) · [frontend/](frontend/) |

The diagrams use Mermaid, which renders natively on GitHub, GitLab and in VS Code.

## Repository layout

```
├── backend/                 FastAPI service
│   ├── app/
│   │   ├── api/             routes, dependency injection, error mapping
│   │   ├── core/            settings, security (OIDC + RBAC), logging, domain errors
│   │   ├── db/              engine / session lifecycle
│   │   ├── infrastructure/  file storage adapter
│   │   ├── models/          ORM entities
│   │   ├── repositories/    search, bulk upsert, audit queries
│   │   ├── schemas/         request / response contracts
│   │   └── services/        CSV parsing, ingestion, pricing logic
│   ├── alembic/             database migrations
│   ├── scripts/             synthetic feed generator for load testing
│   └── tests/
├── frontend/                React SPA
│   └── src/
│       ├── api/             typed API client
│       ├── components/      shared UI primitives
│       ├── features/
│       │   ├── ingestion/   upload, job list, row errors
│       │   └── pricing/     search, results, pagination, edit dialog
│       └── lib/             formatting and query helpers
├── samples/                 example feeds (valid, and with errors)
├── docs/                    architecture deliverables
└── docker-compose.yml
```

## Running the application

### Option A: Docker Compose (PostgreSQL)

```bash
docker compose up --build
```

- Web app: http://localhost:8080
- API docs: http://localhost:8000/docs

Compose runs PostgreSQL, a one-off `migrate` job (`alembic upgrade head`), the API and the nginx-served SPA, which proxies `/api` to the API.

### Option B: local development (SQLite, no Docker)

Requires [uv](https://docs.astral.sh/uv/) and Node.js 20 or later.

```bash
# API on :8000
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --reload

# SPA on :5173 (proxies /api to :8000)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, go to **Feed uploads**, and upload `samples/pricing_feed_valid.csv`, then `samples/pricing_feed_with_errors.csv`.

### Configuration

All settings are environment variables with the `PRICING_` prefix; see [backend/.env.example](backend/.env.example).

| Variable | Default | Purpose |
|---|---|---|
| `PRICING_DATABASE_URL` | `sqlite:///./pricing.db` | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@host/db` |
| `PRICING_STORAGE_DIR` | `./data/uploads` | Where raw feed files are kept |
| `PRICING_MAX_UPLOAD_BYTES` | 512 MB | Upload size limit, enforced while streaming |
| `PRICING_INGESTION_BATCH_SIZE` | 5000 | Rows per upsert transaction |
| `PRICING_AUTH_MODE` | `disabled` | `jwt` enables OIDC token validation (required in production) |
| `PRICING_JWT_JWKS_URL` / `_AUDIENCE` / `_ISSUER` | — | Identity provider settings |
| `PRICING_JWT_ROLES_CLAIM` | `roles` | Claim that holds `pricing.viewer` / `pricing.editor` / `pricing.uploader` |

## API

| Method | Path | Role | Description |
|---|---|---|---|
| `POST` | `/api/v1/ingestions` | uploader | Upload a CSV (multipart `file`). Returns `202` with the job; `409` if the identical file was already ingested |
| `GET` | `/api/v1/ingestions?limit=20` | viewer | Recent ingestion jobs |
| `GET` | `/api/v1/ingestions/{id}` | viewer | Job status and counts |
| `GET` | `/api/v1/ingestions/{id}/errors` | viewer | Rejected rows with line number and reason |
| `GET` | `/api/v1/pricing-records` | viewer | Search: `store_id`, `sku`, `product_name` (contains), `min_price`, `max_price`, `date_from`, `date_to`, `sort` (e.g. `-price_date`), `page`, `page_size` |
| `GET` | `/api/v1/pricing-records/{id}` | viewer | Single record |
| `PATCH` | `/api/v1/pricing-records/{id}` | editor | Update `price` and/or `product_name`; requires the current `version` (`409` if stale) |
| `GET` | `/api/v1/pricing-records/{id}/history` | viewer | Audit trail of manual edits |
| `GET` | `/health/live`, `/health/ready` | — | Liveness and readiness (readiness checks the database) |

### CSV contract

```csv
Store ID,SKU,Product Name,Price,Date
ST00001,SKU-100001,Whole Milk 1L,1.99,2026-11-01
```

- Headers are case-insensitive and column order does not matter (`Store ID`, `store_id` and `StoreId` all work)
- UTF-8, `Date` as `YYYY-MM-DD`, `Price` greater than 0 with up to 4 decimals
- The same `(Store ID, SKU, Date)` updates the existing record; within one file the last occurrence wins

## Quality checks

```bash
cd backend  && uv run pytest && uv run ruff check . && uv run ruff format --check .
cd frontend && npm run typecheck && npm test && npm run build
```

Latest results: 53 backend tests and 6 frontend tests pass, lint is clean, and `alembic check` reports that the models and migrations match.

### Performance check

```bash
cd backend
uv run python scripts/generate_feed.py /tmp/feed.csv --stores 200 --skus 1000
curl -F file=@/tmp/feed.csv http://localhost:8000/api/v1/ingestions
```

On a developer laptop (SQLite, single process), the 200,000-row file (9 MB) ingests in about 2.9 s, roughly 69k rows/s. A product-name *contains* search with a price filter over the result returns in about 70 ms. These numbers are a baseline; production capacity should be measured on PostgreSQL.
