# Dual Engine Feature Mining Method

## Scope

This method targets credit anti-fraud variable mining with two engines:

- `auto_features`: broad statistical mining on entity graph.
- `semantic_features`: hypothesis-driven business variables.

## Process

1. Build shared entity graph.
2. Generate auto features.
3. Generate semantic features by fraud theme.
4. Build constrained composite features.
5. Merge into unified candidate pool.
6. Run selection and stability checks.
7. Promote approved features and update registry.

## Fraud Themes

- Consistency checks
- Short-window velocity
- Cash-out and collusion behavior

## Promotion States

- `selected_for_model`
- `selected_for_rule`
- `watchlist`
- `rejected`
