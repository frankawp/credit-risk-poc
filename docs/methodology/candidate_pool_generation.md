# Candidate Pool Generation

## Sources

- Auto source: DFS output from `Featuretools`.
- Semantic source: business-defined anti-fraud feature groups.
- Composite source: constrained combinations over selected base features.

## Contract

- One row per `SK_ID_CURR`.
- Include `TARGET` in training stage.
- Keep source tag per feature:
  - `auto`
  - `semantic`
  - `composite`

## Guardrails

- Do not run unconstrained all-pairs feature interactions.
- Keep composite generation tied to explicit fraud hypotheses.
- Keep registry metadata for every generated feature.
