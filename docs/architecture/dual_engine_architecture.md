# Dual Engine Candidate Architecture

## Goal

Build a single candidate pool from two independent sources:

- `auto_features`: generated from entity graph + primitives.
- `semantic_features`: handcrafted business features from fraud hypotheses.

Then apply a unified selection layer to produce model-ready and rule-ready features.

## Flow

```mermaid
flowchart LR
    A["Raw Tables"] --> B["Entity Layer"]
    B --> C["Auto Feature Engine"]
    B --> D["Semantic Feature Engine"]
    C --> E["Auto Candidate Set"]
    D --> F["Semantic Candidate Set"]
    E --> G["Composite Feature Builder"]
    F --> G
    E --> H["Unified Candidate Pool"]
    F --> H
    G --> H
    H --> I["Basic Filters"]
    I --> J["Supervised Selection"]
    J --> K["Correlation Grouping"]
    K --> L["Stability Validation"]
    L --> M["Approved Feature Set"]
```

## Output Contracts

- Candidate pool: one row per `SK_ID_CURR`, with `TARGET`.
- Feature registry: source, definition, risk direction, owner, status.
- Selection reports: scorecard, correlation groups, kept/dropped reasons.

## Operational Principles

- Keep feature source labels (`auto` / `semantic` / `composite`).
- Keep selection policy source-agnostic but with source-specific thresholds.
- Keep fraud-rule features in a separate retention policy to avoid accidental deletion.
