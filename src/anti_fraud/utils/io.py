from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT / "configs"
RAW_DIR = ROOT / "data" / "raw" / "home-credit-default-risk"
INTERIM_DIR = ROOT / "data" / "interim"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "outputs" / "reports"
MODEL_DIR = ROOT / "outputs" / "models"
FEATURE_DIR = ROOT / "outputs" / "features"


def load_yaml(name: str) -> dict:
    with (CONFIG_DIR / name).open() as fh:
        return yaml.safe_load(fh)


def ensure_output_dirs() -> None:
    for directory in (INTERIM_DIR, PROCESSED_DIR, REPORT_DIR, MODEL_DIR, FEATURE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def csv_path(name: str) -> Path:
    return RAW_DIR / name


def read_csv(name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(csv_path(name), **kwargs)


def iter_csv(name: str, usecols: list[str] | None = None, chunksize: int = 250_000, **kwargs) -> Iterator[pd.DataFrame]:
    yield from pd.read_csv(csv_path(name), usecols=usecols, chunksize=chunksize, **kwargs)


def read_columns_description() -> pd.DataFrame:
    return pd.read_csv(csv_path("HomeCredit_columns_description.csv"), encoding="cp1252")


def write_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)


def write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def write_markdown(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
