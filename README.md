![CI](https://github.com/ivanrivasgr/Sports_Injury_Risk_Intelligence/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)
![Black](https://img.shields.io/badge/code%20style-black-000000)
![Ruff](https://img.shields.io/badge/linter-ruff-orange)
![License](https://img.shields.io/badge/license-MIT-green)

# Sports Injury Risk — Data Architecture & ML Pipeline

> **"This is not an analysis of outcomes. This is the system required to make reliable analysis possible."**

A production-grade data architecture and ML-ready pipeline for evaluating injury risk in professional football, built as a portfolio project to demonstrate engineering rigor — not to make causal claims.

🔗 **[Live App](https://sportsinjuryriskintelligence-jxgxyr6kp5thzqfbhkyu8w.streamlit.app/)** &nbsp;|&nbsp; 💻 **[GitHub](https://github.com/ivanrivasgr/Sports_Injury_Risk_Intelligence)**

---

## What this is

A 12-page interactive Streamlit application covering:

| Page | Content |
|------|---------|
| 00 · Overview | Project KPIs and system positioning |
| 01 · Problem Framing | Structural question, observable vs proxy variables |
| 02 · Data Sources | 8 sources with bias and limitation analysis |
| 03 · Architecture | Medallion stack (Bronze → Silver → Gold → Feature Store) |
| 04 · Data Model | 6 core tables, grain definitions, join paths |
| 05 · Feature Engineering | Point-in-time correct walkthrough, feature catalogue |
| 06 · Pipeline DAG | Task dependencies, idempotency, partitioning |
| 07 · Observability | DQ checks, PSI drift detection, alert rules |
| 08 · ML Layer | Binary classifier + survival model design, uncertainty quantification |
| 09 · Limitations | Explicit epistemic limitations — every assumption documented |
| 📊 Real Data Dashboard | 88 Real Madrid injury events (2021–2025) from Transfermarkt |
| 🔬 CI/CD & Debug | Live test runner, pipeline debug console, structured log viewer |

---

## Real data

The dashboard uses **88 documented Real Madrid injury events** sourced from Transfermarkt public records and official press communications (2021–2025):

- 25 players across 4 seasons
- 69% muscular injuries
- Peak months: October–November and February–March
- Mendy (9 events), Camavinga (7), Courtois (6)

Every limitation is documented: ~30–40% of injuries are never publicly reported, venue is approximated from the last match before report date, and training injuries are completely unobservable.

**Association ≠ causation. Stated explicitly, repeatedly.**

---

## Architecture

```
Raw Sources (APIs, Batch)
        │
   ┌────▼────┐
   │ Bronze  │  Immutable append-only, schema-on-read, timestamped
   └────┬────┘
        │
   ┌────▼────┐
   │ Silver  │  Entity resolution, schema enforcement, DQ checks
   └────┬────┘
        │
   ┌────▼──────┐
   │ Enriched  │  Cross-source joins, temporal alignment
   └────┬──────┘
        │
   ┌────▼────┐
   │  Gold   │  Rolling workload features, congestion index, injury labels
   └────┬────┘
        │
   ┌────▼──────────┐
   │ Feature Store │  Point-in-time correct, versioned, train/infer consistent
   └───────────────┘
```

---

## Project structure

```
sports_pipeline/
├── app.py                    # Main entry point + global CSS/navigation
├── requirements.txt
├── pyproject.toml
├── .streamlit/
│   └── config.toml           # Theme configuration
├── data/
│   ├── seed_data.py          # Pre-built dataset (88 injury events)
│   ├── pipeline.py           # Gold pipeline, DQ checks, feature computation
│   └── build_dataset.py      # Live scraper (run locally)
├── views/
│   ├── p00_overview.py  →  p11_cicd.py   # All 12 app pages
├── utils/
│   ├── logger.py             # Structured JSONL logger
│   └── exceptions.py         # Typed exception hierarchy
└── tests/
    ├── test_pipeline.py       # Point-in-time leakage guards
    ├── test_seed_data.py      # Schema and contract validation
    └── test_utils.py          # Logger and exception tests
```

---

## Quick start

```bash
git clone https://github.com/ivanrivasgr/Sports_Injury_Risk_Intelligence.git
cd Sports_Injury_Risk_Intelligence
pip install -r requirements.txt
streamlit run app.py
```

To refresh with live scraping (requires network access):
```bash
python data/build_dataset.py --scrape
```

---

## Tech stack

| Category | Tools |
|----------|-------|
| App framework | Streamlit |
| Visualisation | Plotly |
| Data processing | Pandas, NumPy |
| Transform layer (design) | dbt |
| Storage layer (design) | Delta Lake / Apache Iceberg on S3 |
| Data quality (design) | Great Expectations |
| Feature store (design) | Feast |
| Orchestration (design) | Apache Airflow |
| CI/CD | GitHub Actions |

---

## Disclaimer

This system supports **association analysis only**.  
It does not support causal inference.  
All model outputs and performance metrics use **synthetic data**.  
The real dataset contains 88 documented events — insufficient for training a production model.

No output from this system should be used to make decisions about individual players, pitch construction, or scheduling policy without additional causal analysis and domain expert validation.
