# Dual Engine Quickstart

## Prerequisites

- Python virtual environment at `.venv`
- Raw data under `data/raw/home-credit-default-risk`
- `featuretools`, `pandas`, `pyarrow`, `scikit-learn` installed in `.venv`

## Build Candidate Pool

```bash
PYTHONPATH=src .venv/bin/python -m dual_engine.pipelines.run_candidate_pool --sample-size 3000 --max-depth 2
```

## Run Selection

```bash
PYTHONPATH=src .venv/bin/python -m dual_engine.pipelines.run_selection
```

## Run End-to-End

```bash
PYTHONPATH=src .venv/bin/python -m dual_engine.pipelines.run_dual_engine --sample-size 3000 --max-depth 2
```

## Output Paths

- `outputs/candidate_pool/candidate_pool.parquet`
- `outputs/candidate_pool/registry/feature_registry.csv`
- `outputs/selection/selected_features.parquet`
- `outputs/selection/feature_selection_report.md`
