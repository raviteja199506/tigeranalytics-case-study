# 3. Design Decisions

| # | Decision | Why | Trade-off |
|---|---|---|---|
| 1 | One codebase, deployed as an API and a worker | Search and bulk loading scale differently. Microservices aren't worth it for one domain. | Both use the same database |
| 2 | Process uploads in the background and return `202` | Big files would time out over HTTP | Results show up a few seconds later; the UI polls |
| 3 | Store ID + SKU + Date is the unique key, loaded with an upsert | Re-sending a file is safe and makes no duplicates. Unchanged rows aren't rewritten. | A new feed overwrites a manual edit for the same key |
| 4 | Load good rows and report bad ones | One bad row shouldn't block prices for 3,000 stores | A file can be partly loaded, shown as "completed with errors" |
| 5 | Reject identical files using SHA-256 | Stops accidental double uploads | Failed uploads can still be retried |
| 6 | Keep every raw file | Evidence for audits, and jobs can be re-run after a fix | Storage cost, handled with lifecycle rules |
| 7 | PostgreSQL | Unique keys, exact decimals, transactions, JSON for history, fast "contains" search | Needs partitioning at around 500M rows |
| 8 | Version number on each record | Two people editing the same price can't overwrite each other | The second person reloads and tries again |
| 9 | History for manual edits; feed loads tracked by upload job | Full who/what/when for edits without logging millions of bulk rows | Bulk changes are traced per file, not per row |
| 10 | Only price and product name can be edited | Store, SKU and date identify the record. Changing them would make it a different record. | Wrong keys are fixed by re-uploading |
| 11 | Prices stored as `NUMERIC(14,4)` and sent as strings | No rounding errors. Covers currencies with 3 decimals. | Currency comes from the store, not the file |
| 12 | Strict input: UTF-8 and `YYYY-MM-DD` dates | `03/11/2026` means different dates in different countries | Some exports need converting first |
| 13 | Page-based paging, max 200 rows per page | The UI needs "page X of Y" | Bulk extracts need a separate export |
| 14 | Company login (OIDC) with viewer, editor and uploader roles | Single sign-on and least privilege | Login can be turned off locally, but the app won't start that way in production |
| 15 | Plain (sync) SQLAlchemy and an app factory | Parsing uses CPU, so async adds little. The factory makes testing easy. | Concurrency comes from the thread pool |
| 16 | React with TanStack Query and no UI library; search state in the URL | Simple caching and polling, a small bundle (63 KB gzipped), searches can be bookmarked | Some UI parts are built by hand |
