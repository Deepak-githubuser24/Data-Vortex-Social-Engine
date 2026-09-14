# Data Vortex '26 — Rebuilding the Social Engine (Round 1: Phase 1)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Event: Aaruush '26](https://img.shields.io/badge/Event-Aaruush%20'26-orange.svg)](https://aaruush.org)

**Team Name:** Forge-X  
**Institution:** SRM Institute of Science & Technology  
**Challenge:** Data Vortex — Round 1 (Phase 1): Data Intake Restoration  

---

## 📌 Executive Overview

The Social Engine's data intake pipeline suffered severe multi-system corruption. This repository contains the complete, reproducible production pipeline to ingest, clean, validate, and analyze the corrupted intake datasets (`Social_Engine_Posts_Corrupted.csv` and `Social_Engine_Users.csv`).

### Core Engineering Principles
1. **Zero Data Loss:** 100% of all 683 ingested records are strictly accounted for via mathematical row reconciliation.
2. **Zero Synthetic Fabrication:** Total adherence to competition rulebook guidelines prohibiting synthetic imputation (no mean/median filling of missing metrics).
3. **Forensic Auditability:** 888 automated data transformations logged with exact before/after states in `data/clean/repair_log.csv`.
4. **Reproducibility:** A fully automated pipeline executable via a single terminal command or Jupyter Notebook.

---

## 🗂 Repository Structure

```text
├── Data_Vortex_Phase1_Rebuilding_The_Social_Engine.ipynb  # Primary interactive analysis notebook
├── clean_data.py                                          # Standalone automated cleaning pipeline
├── run_eda.py                                             # Automated statistical & visualization script
├── EDA_Report.md                                          # Comprehensive analytical insights report
├── requirements.txt                                       # Pinned runtime dependencies
├── data/
│   ├── raw/
│   │   ├── Social_Engine_Posts_Corrupted.csv             # Raw corrupted input dataset
│   │   └── Social_Engine_Users.csv                       # Raw user profile dataset
│   └── clean/
│       ├── Social_Engine_Posts_Cleaned.csv               # Standardized posts dataset
│       ├── Social_Engine_Posts_Cleaned.json              # Cleaned posts in JSON format
│       ├── Social_Engine_Posts_EmptyText_HeldOut.csv     # Quarantined posts missing text content
│       ├── Social_Engine_Users_Cleaned.csv               # Validated users table
│       ├── Social_Engine_Users_Cleaned.json              # Validated users in JSON format
│       ├── repair_log.csv                                # Full forensic modification audit log
│       └── cleaning_summary.json                         # Execution metadata & reconciliation assertion
└── eda_outputs/
    ├── eda_summary_metrics.json                          # Aggregated statistical data
    └── figures/
        ├── fig1_platform_engagement.png                  # Platform volume & likes distribution
        ├── fig2_brand_analysis.png                       # Brand mentions & sharing rates
        ├── fig3_timeline.png                             # Ingestion timeline dynamics
        └── fig4_correlation.png                          # Metric correlation matrix
```

---

## ⚙️ Quickstart & Reproduction

### 1. Environment Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/Deepak-V/Data-Vortex-Social-Engine.git
cd Data-Vortex-Social-Engine
pip install -r requirements.txt
```

### 2. Run Cleaning Pipeline
Execute the deterministic cleaning script:
```bash
python clean_data.py
```
*Output: Generates all cleaned CSV/JSON files, quarantine sets, and `repair_log.csv` with automated assertion verification.*

### 3. Generate Exploratory Analysis & Figures
Run the automated analytics and visualization suite:
```bash
python run_eda.py
```

### 4. Interactive Jupyter Notebook
Launch Jupyter to explore step-by-step visualizations and code cells:
```bash
jupyter notebook Data_Vortex_Phase1_Rebuilding_The_Social_Engine.ipynb
```

---

## 🔍 Data Transformation Architecture

| Column | Issue Detected | Corrective Action | Justification |
| :--- | :--- | :--- | :--- |
| `post_id` | Duplicate rows | Exact match check (`keep='first'`) | Preserves unique entities without double-counting metrics. |
| `likes` | Negative floats (e.g. `-4812.0`) & missing values | `abs(float(val))` for negative artifacts; preserved `NaN` for missing values | The negative sign was an upstream buffer flip; synthetic imputation is prohibited by competition rules. |
| `platform` | Missing / inconsistent casing | Normalized to Title Case; missing assigned to `'Unspecified'` | Retains post engagement without inventing ungrounded network origins. |
| `text_content`| Double-encoded Mojibake & HTML tags | UTF-8/Latin-1 reversal, regex tag removal, entity unescaping | Restores textual fidelity for downstream NLP without corrupting semantics. |
| `text_content`| Blank / `NULL` posts | Segregated to `Social_Engine_Posts_EmptyText_HeldOut.csv` | Protects macro-metrics while shielding NLP models from empty strings. |
| `timestamp` | Epoch (seconds/ms), ISO 8601, DD-MM-YYYY | Normalized to UTC ISO 8601 string (`timestamp_utc`) | Harmonizes cross-timezone event ordering; arithmetic proof verifies day-first format. |

---

## 📊 Summary of Insights

1. **Platform Engagement**: Reddit and Twitter drive the highest average likes per post (~2,560), while Facebook generates the highest comment density (536.8 comments/post).
2. **Brand Affinity**: Google and Apple lead in total mention volume (~55 and ~51 mentions), with Nike generating the highest conversational engagement (578.7 comments/post).
3. **Metric Independence**: Correlation analysis confirms that likes, shares, and comments operate independently ($|r| < 0.06$).
4. **Demographic Reach**: Posts originate across 10+ major global languages and 20+ metropolitan centers, with mid-tier creators (10k–30k followers) matching high-follower accounts in average engagement.

---
