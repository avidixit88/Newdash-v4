# NextCure Signal Room v1.4

Backend-ready Streamlit scaffold for the Clinical Intelligence Console rebuild.

## What changed from v1.3

v1.3 was a one-file prototype. v1.4 separates the build into real layers so the system can later move to a backend API and database without rewriting the executive UI.

## Project structure

```text
app.py                          # Streamlit UI shell only
src/config.py                   # Preset lanes, queries, app constants
src/clinicaltrials_client.py    # ClinicalTrials.gov ingestion boundary
src/normalization.py            # Registry parsing, field cleaning, lane classification
src/analytics.py                # Analysis bundle, signal-feed rules, aggregation helpers
src/charts.py                   # Plotly chart builders and shared chart theme
src/ui.py                       # Premium Streamlit UI components
src/styles.py                   # Custom CSS
src/sample_data.py              # Offline fallback/demo data
data/cache/                     # Reserved for future cache/database export artifacts
tests/                          # Lightweight sanity tests
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Production path

The current boundary is:

```text
Streamlit UI -> analytics service -> ClinicalTrials.gov client -> normalization layer
```

Later production path:

```text
Frontend/Streamlit -> FastAPI backend -> Postgres/Supabase -> scheduled registry ingestion -> auth/admin controls
```

The core rule is preserved: Streamlit is the interface, not the brain.


## v1.5 changes

- Replaced vague `Phase not listed` with two distinct executive-ready labels:
  - `Not Applicable / Non-phased Study` when ClinicalTrials.gov returns `NA`
  - `Phase Missing From Registry` when the phase field is absent
- Upgraded combination therapy intelligence from a simple keyword count to a structured ADC/oncology classifier.
- Added partner-class extraction for IO/checkpoint, chemo/platinum/taxane, anti-VEGF, PARP/DNA damage, HER2/EGFR/targeted pathway, endocrine/hormonal, radiation/radiopharmaceutical, and ADC/multi-ADC strategies.
- Added combination confidence and evidence fields so every classification is auditable.

## Backend readiness note

The Streamlit layer remains intentionally thin. Ingestion, normalization, analytics, charts, config, and UI components are separated so the same backend logic can later move behind FastAPI, a scheduled worker, and Postgres/Supabase without rewriting the executive interface.
