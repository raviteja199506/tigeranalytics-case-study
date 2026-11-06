# 4. Non-Functional Requirements

## Sizing

| | Estimate |
|---|---|
| Stores | 3,000 |
| SKUs per store | ~25,000 (75M store-SKU pairs) |
| Price changes per day | 1.5M to 4M rows |
| Full chain snapshot | ~75M rows, ~3.4 GB |
| Rows kept for 2 years | 1B to 3B |
| Users | ~3,300, about 300 at peak |

## How each requirement is met

"Built" means it's in this repo. "Platform" means it comes from cloud setup.

| Area | Target | How | |
|---|---|---|---|
| Scale | Bulk loads don't slow down search | Uploads are processed separately. API and workers scale on their own. | Built / Platform |
| Scale | Memory stays flat for any file size | Files are streamed in 1 MB chunks and saved 5,000 rows at a time | Built |
| Scale | Billions of rows | Indexes per search type; monthly partitions and read replicas later | Built / Platform |
| Speed | Search under 500 ms | Indexes and a page size cap. 72 ms on 200k rows locally. | Built |
| Speed | 20k+ rows/s per worker | Batch upserts that skip unchanged rows. 69k rows/s locally on SQLite. | Built |
| Availability | 99.9% | 3+ API instances across zones, multi-zone database, SPA served from a CDN | Platform |
| Availability | Health checks | `/health/live` and `/health/ready` (checks the database) | Built |
| Recovery | A crash mid-file doesn't break anything | Each batch commits on its own. Re-running a file is safe. | Built |
| Recovery | RPO 15 min, RTO 1 hour | Database and files copied to a second region | Platform |
| Data quality | No duplicate prices | Unique key on store, SKU and date | Built |
| Data quality | No bad prices saved | Checked in code and by a database rule (price > 0) | Built |
| Data quality | No lost edits | Version check returns 409 on a stale edit | Built |
| Security | Company login, least privilege | OIDC tokens and three roles checked on each endpoint | Built |
| Security | Safe input | Strict schemas, unknown fields rejected, whitelisted sort, parameterised SQL | Built |
| Security | Safe uploads | Only `.csv`, size limit, server-made file names | Built |
| Security | Browser and network | Security headers and strict CORS built; TLS, WAF and encryption at rest from the platform | Built / Platform |
| Audit | Who changed what and when | History row saved with every edit and shown in the UI | Built |
| Audit | Where a price came from | Each record links to its upload job; raw files kept | Built |
| Monitoring | Logs that can be traced | JSON logs with a request ID on every call | Built |
| Monitoring | Alerts and dashboards | Metrics, traces, failed-upload alerts | Platform |
| Maintenance | Clean, tested code | Layered code, linting, strict TypeScript, 59 tests | Built |
| Deployment | Same result everywhere | Locked dependencies, Docker images running as non-root, versioned migrations | Built |
| Accessibility | WCAG 2.1 AA | Labelled inputs, sortable tables readable by screen readers, keyboard-friendly dialog, visible focus | Built |
| Multi-country | Any language and locale | UTF-8 names, numbers and dates formatted to the user's locale, UTC timestamps | Built |
| Cost | Pay for what's used | Static SPA on a CDN, workers scale to zero, old data archived | Platform |

The local numbers are a starting point. Measure again on production PostgreSQL.
