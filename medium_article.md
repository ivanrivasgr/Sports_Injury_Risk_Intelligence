# Building a Production-Grade Sports Injury Risk Pipeline: Architecture First, Conclusions Never

*A data engineering and ML systems design project using Real Madrid injury data (2021–2025)*

---

Most sports data projects start with a hot take and work backwards to the data.

This one starts with the system.

The goal of this project is not to answer whether Real Madrid's pitch causes injuries, whether schedule congestion is the culprit, or whether any specific player is "injury-prone." Those are questions that require causal inference frameworks, controlled conditions, and domain expertise that no public dataset can fully support.

The goal is to demonstrate what a **trustworthy, production-ready data system** would look like if you wanted to ask those questions rigorously — and what it would require.

This distinction is not a cop-out. It's the point.

---

## The Problem With Sports Injury Analysis

Sports injury analysis is everywhere. Every major outlet, every stats site, every pundit has an opinion backed by numbers.

Most of it is noise.

Not because the journalists are bad, but because the underlying data systems are not designed for the question being asked. The data is incomplete, the injury labels are approximate, the confounders are unobserved, and the causal identification strategy is missing entirely.

Before a single query runs, a rigorous system needs to define four things explicitly:

**1. The structural question** — "What data architecture is required to evaluate injury risk at scale?" — not "does the pitch cause injuries?"

**2. What is actually observable** — match appearances (yes), reported injuries (partially), pitch conditions (barely), GPS workload (no, unless you have a club partnership)

**3. The assumptions required** — injury reports cover maybe 60-70% of real events; venue is assigned to the last match before a public announcement; player quality and medical staff quality are unobserved confounders

**4. What model outputs actually represent** — conditional association scores, not causal estimates

Define those four things upfront, and every downstream decision follows logically.

---

## The Architecture

The system follows a **Medallion Architecture** with five layers, a Feature Store, and a full observability stack.

### 🥉 Bronze Layer — Immutable Raw Storage

Every data source lands here exactly as received: no transformations, no cleaning, no schema enforcement. Records carry a `source_id`, `ingestion_ts`, and `batch_id`.

The key property is immutability. Bronze is append-only. If a source sends bad data, we fix it downstream — we never modify what landed.

Technology: Delta Lake on S3, Parquet format, partitioned by `(source, date)`.

### 🥈 Silver Layer — Clean and Validated

This is where data earns the right to be used:

- **Schema enforcement** via registered schemas (Avro/Protobuf)
- **Entity resolution**: `player_id`, `match_id`, and `team_id` are normalized across sources. A player named "Vinicius Jr" on one source and "Vinícius Júnior" on another resolves to the same canonical UUID
- **Data quality checks**: completeness, range validation, referential integrity
- **Deduplication** via deterministic merge keys

Technology: dbt Core + Great Expectations, schema registry.

### 📦 Enriched Layer — Cross-Source Joins

Appearances join to matches. Matches join to environmental conditions. The temporal spine is established here: every event is pinned to `kickoff_datetime` as the reference point.

No feature aggregations happen at this layer — that's reserved for Gold.

### 🥇 Gold Layer — ML-Ready Features

This is the heart of the system. Every feature is:

- **Point-in-time correct** — features for a training example anchored at match `m` use only data available before `kickoff_datetime(m)`
- **Explicitly defined** — rolling 7/14/30-day workload windows, schedule congestion index (average rest days over 30d), injury binary label (with temporal lag)
- **Separated** into observed variables (minutes played, position) and derived aggregations (rolling workload, congestion tier)

The label construction deserves special attention. The `injured_next_7d` label looks ahead from the anchor match — it is **only ever used in training dataset construction**, never exposed during inference. This distinction is enforced at the Feature Store layer.

### 🧠 Feature Store

Features are versioned (`player_workload_v1`, `player_workload_v2`), stored with computation timestamps, and support point-in-time joins for historical training. The offline store serves batch training; the online store serves inference.

This ensures identical feature definitions between training and production — one of the most common sources of silent failure in ML systems.

---

## The Data Model

Six core tables, each with an explicitly defined grain:

| Table | Grain | Key Relationship |
|-------|-------|-----------------|
| `players` | One row per player | Canonical UUID across sources |
| `teams` | One row per team | Slowly changing dimension |
| `matches` | One row per match | Central fact table |
| `appearances` | One row per player × match | Bridge between players and matches |
| `injuries` | One row per injury event | Joined to last match before report |
| `environmental_conditions` | One row per match | 1:1 with matches |

The grain definition is non-negotiable. Without it, every aggregation query is ambiguous, and every join risks fan-outs that silently inflate metrics.

---

## The Real Data

The dashboard uses 88 documented injury events sourced from **Transfermarkt public records** and official Real Madrid press communications (2021–2025).

This is not comprehensive. It is not even close to complete. And that is documented explicitly.

**What the data shows:**

- 69% of documented injuries are muscular in nature
- Injury frequency peaks in October–November (congested early-season fixture schedule) and February–March (mid-season fatigue accumulation)
- Players with most documented injuries in the dataset: Ferland Mendy (9), Eduardo Camavinga (7), Thibaut Courtois (6), Eder Militao (6)
- Severe injuries (ACL ruptures to Courtois, Militao ×2, Alaba ×2, Carvajal) skew the days-missed distribution significantly

**What the data does not show:**

- Whether any of these injuries are causally linked to pitch conditions, schedule, or any other factor
- The ~30-40% of injuries that were never publicly reported
- Training ground injuries (entirely unobservable from public sources)
- The exact moment an injury occurred (only the date of public announcement)

Every chart in the dashboard carries this context. Disclaimers are not footnotes — they are part of the design.

---

## The Pipeline DAG

The pipeline is designed around four principles:

**Idempotency** — every task can be re-run for the same date partition without changing the output. This makes debugging safe and retries automatic.

**Incremental processing** — only new data is processed on each run. Full refreshes are reserved for schema migrations.

**Dependency-first scheduling** — no task runs until all upstream dependencies have completed and passed validation. DQ failures block downstream execution.

**Partition-aware execution** — all jobs operate on `(date)` partitions, enabling parallelism and targeted reprocessing.

The DAG has 16 tasks across five groups: ingestion, validation, Bronze write, Silver transforms, Gold feature computation, and Feature Store push — with an independent DQ monitoring branch running in parallel.

---

## Observability

A pipeline without observability is a liability.

The system runs three types of monitoring:

**Data quality checks** run after every Silver transform. CRITICAL checks (uniqueness violations, null primary keys) block downstream tasks immediately. HIGH checks trigger alerts but allow continuation. Pass rates below 99% for any CRITICAL check raise a PagerDuty alert.

**Drift detection** uses Population Stability Index (PSI) on key features. PSI > 0.10 triggers a warning; PSI > 0.25 triggers an alert and flags the affected feature for human review. Seasonal features (like temperature) are expected to drift — the system distinguishes expected from unexpected drift.

**Pipeline health** tracks run duration, record counts, and failure rates. A 30% drop in daily record count versus the 7-day average triggers an ingestion alert before downstream consumers are affected.

---

## The ML Layer

The modeling layer is deliberately secondary to the pipeline.

Two options are designed but not deployed:

**Option A: Binary Classifier** (XGBoost/LightGBM) predicts P(injury in next 7 days) per player-match. Training uses time-series cross-validation — no random splits that leak future information. Class imbalance (~12% positive) is handled via class weights.

**Option B: Survival Model** (Cox Proportional Hazards or Random Survival Forest) models time-to-injury and handles censored observations — players who leave the dataset without an observed injury event.

Both options use SHAP for feature attribution, which serves model auditing, not decision-making. High SHAP importance does not imply causation.

The most important feature engineering choice is the temporal split: the hold-out set is always the most recent season. There is no exception.

---

## What This Project Is Not

This project does not:

- Claim that pitch conditions cause injuries
- Provide injury risk scores for real players
- Replace medical or performance staff judgment
- Generalize beyond the observed leagues and time period

This project does:

- Demonstrate what production-level thinking looks like in data engineering
- Show how to be honest about data limitations at system design time
- Build a reusable template for association analysis in sports contexts
- Make the distinction between "we can measure this" and "we can conclude this" visible

---

## Running It Yourself

```bash
# Clone / unzip
pip install -r requirements.txt
streamlit run app.py

# Live scraping (requires network — Transfermarkt + Open-Meteo)
python data/build_dataset.py --scrape
```

The app runs on Streamlit Cloud with no external dependencies. The seed dataset is bundled. The scraper runs locally when you have network access.

---

## Closing Thought

The sentence I kept returning to while building this:

> *"This is not an analysis of outcomes. This is the system required to make reliable analysis possible."*

In data engineering, the discipline to say what your system cannot conclude — and to build that constraint into the design — is harder than building the pipeline itself.

It is also what separates a trustworthy system from a convincing-looking one.

---

*Live app: [Streamlit Cloud URL]*
*Code: [GitHub URL]*
*LinkedIn: [LinkedIn post URL]*

---

**Tags:** Data Engineering · MLOps · Feature Engineering · Sports Analytics · Python · Streamlit · dbt · Delta Lake · Production ML
