# Outputs Viewer

## Purpose

Use the Streamlit viewer to inspect `outputs/` artifacts by workflow step:

1. candidate pool generation
2. feature registry
3. feature selection

## Run

```bash
PYTHONPATH=. .venv/bin/streamlit run app/streamlit_app.py
```

## Notes

- The viewer is read-only.
- It reads the latest files under `outputs/`.
- It explicitly shows lineage mismatches when some outputs are sampled and others are full population.
- Composite features should also expose `outputs/candidate_pool/registry/composite_feature_spec.csv` so the page can show formula, base features, and business notes.
