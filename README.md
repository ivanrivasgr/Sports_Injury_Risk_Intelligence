# Sports Injury Risk — Data Architecture Blueprint

A production-grade data architecture and ML-ready pipeline for evaluating
injury risk in professional football. Built as a portfolio / LinkedIn project
to demonstrate engineering rigor, not to make causal claims.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure

```
sports_pipeline/
├── app.py                  # Main entry point + navigation
├── requirements.txt
├── data/
│   ├── seed_data.py        # Pre-built dataset (Transfermarkt + press reports)
│   └── build_dataset.py    # Live scraper (run locally: python build_dataset.py --scrape)
└── pages/
    ├── p00_overview.py     # Project KPIs and positioning
    ├── p01_framing.py      # Problem framing
    ├── p02_sources.py      # 8 data sources with bias/limitation analysis
    ├── p03_architecture.py # Medallion architecture
    ├── p04_datamodel.py    # 6 core tables
    ├── p05_features.py     # Feature engineering walkthrough
    ├── p06_dag.py          # Pipeline DAG
    ├── p07_observability.py# DQ checks, drift, alerting
    ├── p08_ml.py           # ML layer
    ├── p09_limitations.py  # Explicit limitations
    └── p10_dashboard.py    # Real Data Dashboard (88 injury events, 2021-25)
```

## Real Data

The dashboard (📊 Real Data Dashboard) uses 88 documented Real Madrid injury events
sourced from Transfermarkt public records and official press communications (2021-2025).

To refresh with live scraping (requires network):
```bash
python data/build_dataset.py --scrape
```

## Disclaimer

This system supports **association analysis only**.
It does not support causal inference.
All model outputs and visualizations use **synthetic data**.
