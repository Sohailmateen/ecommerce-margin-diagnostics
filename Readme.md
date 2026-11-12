
# E-Commerce Margin Erosion & Customer Lifecycle Diagnostics

An end-to-end data analytics engineering and decision-science project investigating why top-line e-commerce revenue growth often masks underlying contribution margin compression and post-purchase customer churn.

Built across **PostgreSQL**, **Python (`pandas`, `SQLAlchemy`, `SciPy`, `statsmodels`)**, **Excel**, and **Power BI**, this repository simulates a real-world enterprise analytics workflow: ingesting raw transactional logs into a dimensional data warehouse, running non-parametric and logistic regression root-cause diagnostics, modeling financial recovery scenarios, and delivering an executive decision dashboard.

---

## Executive Summary & Business Impact

* **Dataset Scope:** 99,441 orders, 112,650 line items, 103,886 payment records, and 99,224 customer reviews (Olist Brazilian E-Commerce dataset; **96,478 delivered orders** generating **$13.22M** in gross revenue and **$4.90M** in baseline net contribution margin).
* **Core Business Problem:** Despite strong top-line GMV expansion, net contribution margins face structural leakage driven by small-basket shipping friction, carrier SLA breaches, and low repeat-purchase retention.
* **Projected Financial Impact:** Implementing three data-backed operational policies yields an estimated **+$87,965.92** in incremental net margin recovery under the Base Case scenario (ranging from **+$47,204** Conservative to **+$140,860** Aggressive).

---

## System Architecture

```text
[Raw Kaggle CSVs (6 Tables)]
             │
             ▼
[Python Ingestion Pipeline] ──► Schema validation, timestamp coercion, deduplication (SQLAlchemy)
             │
             ▼
[PostgreSQL Data Warehouse] ──► 3-Layer Architecture: staging ─► dw (Star Schema) ─► analytics (Views)
             │
             ├──► [Python Statistical Diagnostics] ──► Mann-Whitney U Test & Multivariate Logistic Regression
             │
             ├──► [Excel Financial Simulator]      ──► Unit Economics & 3-Scenario Sensitivity Model
             │
             └──► [Power BI Executive Dashboard]   ──► Star Schema DAX, Cohort Matrix & Waterfall Bridge
```

---

## Key Analytical Findings

### 1. The Small-Basket Freight Trap (Unit Economics Leakage)

* Orders under $25 ($n = 9,702$) average $18.40 in item revenue against $14.24 in shipping fees—an 84.73% freight-to-price ratio (compared to 9.69% on orders over $250).
* Sub-$25 orders generate just $3.79 in average net margin and account for 335 of the 350 unprofitable orders (95.7%) across the entire marketplace.

### 2. The Delivery Delay "Rating Cliff" (Mann-Whitney $U$ Test)

* Because 1–5 star review scores are ordinal and heavily skewed, a non-parametric Mann-Whitney $U$ test was used to compare on-time vs. delayed deliveries ($U = 524,785,358, \; p < 0.0001$).
* **On-Time Orders ($n = 88,171$):** Mean review score of 4.29 (Median 5.0), with a 6.59% 1-star review rate.
* **Delayed Orders ($n = 7,661$):** Mean review score collapses to 2.57 (Median 2.0).
* **Severity Decay Curve:** 1-star review rates surge from 6.59% (on-time) $\rightarrow$ 25.11% (1–3 days late) $\rightarrow$ 58.47% (4–7 days late) $\rightarrow$ 69.76% (8+ days late)—disproportionately impacting high-margin orders ($58.71 avg net margin).

### 3. Repeat Purchase & Churn Drivers (Logistic Regression)

* Modeling first-order customer experiences via multivariate logistic regression (`statsmodels.Logit`, $n = 92,743$ unique customers):
* **Carrier SLA Delay (`is_delayed`):** Reduces the odds of a repeat purchase by 12.51% ($\text{Odds Ratio} = 0.8749, \; p = 0.0988$).
* **Order Ticket Size (`gross_revenue`):** Statistically significant negative coefficient ($p = 0.0037$), confirming that high-ticket durable goods naturally exhibit lower short-term reorder frequency than everyday consumables.

---

## Strategic Recommendations & Scenario Model

| Policy Lever                         | Operational Action                                                                                            | Base Case Assumption                                                       | Incremental Margin Gain |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------- |
| **1. Minimum Basket Bundling** | Introduce a $25 minimum order threshold or multi-item bundle incentive to offset fixed handling/freight costs | Convert 25% of sub-$25 orders into $25–$50 baskets (+$8.03/order lift)    | +$19,470.82             |
| **2. Carrier SLA Enforcement** | Reallocate volume away from underperforming regional carriers exceeding 3-day delays                          | Cut SLA delays by 30% (recovering 12.51% repeat odds at $50.82 avg margin) | +$14,619.10             |
| **3. Warehouse Automation**    | Streamline pick-and-pack fulfillment workflows to lower per-unit handling fees                                | Save $0.50/item across 112,650 items                                       | +$56,325.00             |
| **Total Base Case Recovery**   | **Combined Bottom-Line Impact**                                                                         | **+66 bps Net Margin Lift**                                          | **+$87,965.92**   |

---

## Executive Dashboard Preview (Power BI)

* **Page 1: Executive Margin & Growth Scorecard**
  Tracks top-line GMV ($13.22M) against Net Contribution Margin ($4.90M / 37.08%), SLA Delay Rate (8.11%), regional delivery bottlenecks, and category-level profitability.

![Executive Margin Scorecard](<docs/images/Executive Margin & Growth Scorecard.png>)

* **Page 2: Root-Cause Leakage Diagnostics**
  Visualizes the statistical findings from Python: the review score cliff across SLA delay buckets, the 84.7% freight-to-price spike in sub-$25 orders, and a monthly cohort retention matrix.

![Root-Cause Leakage Diagnostics](<docs/images/Root-Cause Leakage Diagnostics (The Statistical Proof).png>)

* **Page 3: Strategic Profit Recovery Simulator**
  Dynamic waterfall bridge walking from Baseline Net Margin ($4.90M) through each operational lever to Projected Net Margin ($4.99M).

![Profit Recovery Simulator](<docs/images/Strategic Action & Profit Recovery Simulator.png>)

---

## Repository Structure

```text
ecommerce-margin-diagnostics/
├── data/
│   ├── raw/                        # Raw Kaggle Olist CSV files (gitignored)
│   └── processed/                  # Statistical summary tables exported for Excel/BI
├── docs/
│   └── images/                     # Power BI dashboard screenshots
├── models/
│   └── financial_scenario_model.xlsx # Interactive 3-scenario Excel sensitivity workbook
├── pbix/
│   └── executive_margin_dashboard.pbix # Power BI report (Star Schema + DAX)
├── sql/
│   ├── 01_staging_ddl.sql          # Raw staging schema & tables
│   ├── 02_dim_fact_ddl.sql         # Dimensional Star Schema (Dims & Facts)
│   └── 03_analytics_views.sql      # Cohort retention & order diagnostics views
├── src/
│   ├── ingest.py                   # Automated Python-to-PostgreSQL ETL script
│   ├── stats_diagnostics.py        # Mann-Whitney U & Logistic Regression pipeline
│   └── build_excel_model.py        # Automated openpyxl financial model generator
├── .env.example                    # Database environment variable template
├── requirements.txt                # Python dependencies
└── README.md
```

---

## How to Reproduce Locally

### 1. Clone the Repository & Install Dependencies

```bash
git clone [https://github.com/](https://github.com/Sohailmateen/ecommerce-margin-diagnostics.git
cd ecommerce-margin-diagnostics
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure PostgreSQL & Ingest Data

* Download the **Olist Brazilian E-Commerce Dataset** and place the CSVs into `data/raw/`.
* Create a PostgreSQL database named `ecommerce_analytics` and configure `.env` with `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME`.
* Execute `sql/01_staging_ddl.sql`, run the ingestion pipeline, and build the warehouse:

```bash
python src/ingest.py
```

* Execute `sql/02_dim_fact_ddl.sql` and `sql/03_analytics_views.sql` in PostgreSQL.

### 3. Run Statistical Diagnostics & Generate Excel Model

```bash
python src/stats_diagnostics.py
python src/build_excel_model.py

```

### 4. Open Power BI Report

* Open `pbix/executive_margin_dashboard.pbix` in Power BI Desktop and refresh the PostgreSQL connection.
