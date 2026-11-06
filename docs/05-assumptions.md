# 5. Assumptions

These need confirming with the business.

## Data

| # | Assumption | If wrong |
|---|---|---|
| 1 | Files are CSV with a header row: Store ID, SKU, Product Name, Price, Date. Columns can be in any order. | Add a column mapping per source |
| 2 | Files are UTF-8 | Add encoding detection |
| 3 | Date is the day the price applies, as `YYYY-MM-DD` | Add date formats per country |
| 4 | There's one price per store, SKU and day. The latest feed wins. | Add a time to the key |
| 5 | Price is in the store's local currency, uses `.` for decimals, and has up to 4 decimal places | Add a currency column |
| 6 | Store country, currency and timezone come from an existing store master system | Add them to the file |
| 7 | Store IDs and SKUs are unique across the whole chain | Add country to the key |
| 8 | A file can cover one store or many, and can hold changes only. Missing rows aren't deleted. | Add a "replace all" option |
| 9 | Product name in the feed is for display only. The product catalogue lives elsewhere. | Check SKUs against the catalogue |

## Process

| # | Assumption | If wrong |
|---|---|---|
| 10 | Uploads happen in the UI for now. Automatic drops can reuse the same pipeline later. | No change needed |
| 11 | Loading the good rows and reporting the bad ones is acceptable | Add an all-or-nothing mode |
| 12 | A new feed overrides an earlier manual fix for the same key | Add a "locked" flag |
| 13 | Edits go live right away, with no approval step | Add an approval workflow |
| 14 | The company login supports OIDC and can send roles | Map groups to roles |
| 15 | Deleting records isn't needed | Add soft delete |

## Platform

| # | Assumption | If wrong |
|---|---|---|
| 16 | Managed PostgreSQL and file storage are available | Storage and database are behind interfaces, so they're easy to swap |
| 17 | Data residency is handled with regional deployments | Use a single region if it isn't needed |
| 18 | Users have up-to-date browsers | Add polyfills |
| 19 | 2 years of history stays searchable; older data is archived | Resize partitions |
| 20 | The UI is in English for now | Add translations |
