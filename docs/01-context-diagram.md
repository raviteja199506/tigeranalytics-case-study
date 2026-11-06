# 1. Context Diagram

The Pricing Feed Platform holds store-level prices for the whole chain. Analysts upload CSV feeds, store and category managers search them, and pricing staff fix mistakes.

```mermaid
flowchart LR
    classDef person fill:#1d4ed8,stroke:#1e3a8a,color:#fff
    classDef system fill:#0f766e,stroke:#134e4a,color:#fff
    classDef external fill:#475569,stroke:#1e293b,color:#fff
    classDef future fill:#94a3b8,stroke:#475569,color:#0f172a,stroke-dasharray: 5 5

    analyst["Pricing Analyst<br/>uploads feeds, fixes prices"]:::person
    manager["Store / Category Manager<br/>searches prices"]:::person
    support["Support<br/>watches uploads"]:::person

    platform["Pricing Feed Platform<br/>upload · validate · store · search · edit"]:::system

    idp["Company login (OIDC)"]:::external
    stores["Store pricing systems<br/>3,000 stores"]:::external
    mdm["Store master data"]:::future
    pos["POS / ERP"]:::future
    lake["Data lake / BI"]:::future
    obs["Monitoring"]:::external

    stores -- "CSV files" --> analyst
    analyst -- "upload, edit" --> platform
    manager -- "search" --> platform
    support -- "job status, row errors" --> platform
    platform -- "check token and roles" --> idp
    platform -. "store country, currency" .-> mdm
    platform -. "price changes" .-> pos
    platform -. "daily extract" .-> lake
    platform -- "logs" --> obs
```

Solid lines are built. Dashed lines are planned integrations and are out of scope here.

| Who | What they do | Role |
|---|---|---|
| Pricing analyst | Uploads feeds, reviews rejected rows, fixes prices | uploader, editor, viewer |
| Store / category manager | Searches prices | viewer |
| Support | Checks upload status and failures | viewer |

**In scope:** CSV upload and validation, saving prices, safe re-uploads, search, editing with conflict checks, change history, login and roles.

**Out of scope:** price approvals, promotions, sending prices to POS, store master data, currency conversion.
