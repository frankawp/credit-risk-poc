# Feature Registry

This directory stores feature definitions and lifecycle states.

## Required Fields

- `feature_name`
- `feature_source` (`auto` / `semantic` / `composite`)
- `source_table`
- `business_definition`
- `risk_direction`
- `owner`
- `status` (`candidate` / `selected_for_model` / `selected_for_rule` / `watchlist` / `rejected`)

## Suggested Files

- `auto_features.md`
- `semantic_features.md`
- `composite_features.md`
- `rejected_features.md`
