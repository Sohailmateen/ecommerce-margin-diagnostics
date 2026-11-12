import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from scipy import stats
import statsmodels.api as sm
from dotenv import load_dotenv

# 1. Connect to PostgreSQL Data Warehouse
load_dotenv()
DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DB_URL)

def load_diagnostics_data():
    print("Fetching analytics.vw_order_diagnostics from PostgreSQL...")
    query = "SELECT * FROM analytics.vw_order_diagnostics;"
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df):,} delivered orders.\n")
    return df

def analyze_unit_economics(df):
    """Hypothesis 1: Small-Basket Margin Erosion & Break-Even Analysis"""
    print("=" * 60)
    print("HYPOTHESIS 1: UNIT ECONOMICS & BASKET SIZE LEAKAGE")
    print("=" * 60)

    # Create basket value tiers
    bins = [0, 25, 50, 100, 250, np.inf]
    labels = ["1. Under $25", "2. $25 - $50", "3. $50 - $100", "4. $100 - $250", "5. Over $250"]
    df["basket_tier"] = pd.cut(df["gross_revenue"], bins=bins, labels=labels)

    tier_summary = df.groupby("basket_tier", observed=False).agg(
        total_orders=("order_id", "count"),
        avg_order_value=("gross_revenue", "mean"),
        avg_freight=("freight_revenue", "mean"),
        avg_freight_ratio_pct=("freight_to_price_ratio", "mean"),
        total_net_margin=("net_margin", "sum"),
        avg_net_margin=("net_margin", "mean"),
        unprofitable_orders=("net_margin", lambda x: (x < 0).sum())
    ).reset_index()

    tier_summary["unprofitable_rate_pct"] = (
        tier_summary["unprofitable_orders"] / tier_summary["total_orders"] * 100
    ).round(2)

    print(tier_summary.to_string(index=False))
    print("\n")
    return tier_summary

def test_delivery_delay_impact(df):
    """Hypothesis 2: Mann-Whitney U Test on SLA Delays vs. Review Scores"""
    print("=" * 60)
    print("HYPOTHESIS 2: LOGISTICS SLA DELAY VS. CUSTOMER SATISFACTION")
    print("=" * 60)

    valid_reviews = df.dropna(subset=["avg_review_score"]).copy()
    on_time = valid_reviews[valid_reviews["is_delayed"] == False]["avg_review_score"]
    delayed = valid_reviews[valid_reviews["is_delayed"] == True]["avg_review_score"]

    # Mann-Whitney U Test (non-parametric test for skewed ordinal scores)
    u_stat, p_val = stats.mannwhitneyu(on_time, delayed, alternative="two-sided")

    print(f"On-Time Orders (n={len(on_time):,}): Mean Score = {on_time.mean():.2f}, Median = {on_time.median():.1f}")
    print(f"Delayed Orders (n={len(delayed):,}): Mean Score = {delayed.mean():.2f}, Median = {delayed.median():.1f}")
    print(f"Mann-Whitney U Statistic: {u_stat:,.0f} | p-value: {p_val:.4e}")

    if p_val < 0.05:
        print("RESULT: Statistically significant drop in customer satisfaction due to late delivery (p < 0.05).\n")
    else:
        print("RESULT: No statistically significant difference.\n")

    # Bucket by delay severity to quantify margin/rating decay
    delay_bins = [-1, 0, 3, 7, np.inf]
    delay_labels = ["On-Time (0 days)", "Minor Delay (1-3d)", "Moderate Delay (4-7d)", "Severe Delay (8d+)"]
    valid_reviews["delay_bucket"] = pd.cut(valid_reviews["sla_delay_days"], bins=delay_bins, labels=delay_labels)

    delay_summary = valid_reviews.groupby("delay_bucket", observed=False).agg(
        orders=("order_id", "count"),
        avg_review=("avg_review_score", "mean"),
        one_star_rate_pct=("avg_review_score", lambda x: (x <= 1.5).mean() * 100),
        avg_net_margin=("net_margin", "mean")
    ).reset_index()

    print(delay_summary.to_string(index=False))
    print("\n")
    return delay_summary

def model_repeat_purchase_drivers(df):
    """Hypothesis 3: Logistic Regression on Customer Retention (Repeat Purchase)"""
    print("=" * 60)
    print("HYPOTHESIS 3: LOGISTIC REGRESSION ON REPEAT PURCHASE DRIVERS")
    print("=" * 60)

    # Identify repeat customers using customer_unique_id
    customer_orders = df.groupby("customer_unique_id")["order_id"].transform("count")
    df["is_repeat_customer"] = (customer_orders > 1).astype(int)

    # Sort by purchase_date and take each customer's FIRST order experience
    first_orders = (
        df.sort_values("purchase_date")
        .drop_duplicates(subset=["customer_unique_id"], keep="first")
        .dropna(subset=["avg_review_score", "freight_to_price_ratio", "gross_revenue"])
        .copy()
    )

    first_orders["is_delayed_int"] = first_orders["is_delayed"].astype(int)

    features = ["is_delayed_int", "avg_review_score", "freight_to_price_ratio", "gross_revenue"]
    X = sm.add_constant(first_orders[features])
    y = first_orders["is_repeat_customer"]

    logit_model = sm.Logit(y, X).fit(disp=False)
    print(logit_model.summary())

    # Calculate Odds Ratios for business interpretation
    odds_ratios = pd.DataFrame({
        "Feature": features,
        "Odds_Ratio": np.exp(logit_model.params[features]).round(4),
        "Pct_Change_in_Odds": ((np.exp(logit_model.params[features]) - 1) * 100).round(2),
        "P_Value": logit_model.pvalues[features].round(4)
    })
    print("\n--- Business Interpretation (Odds Ratios) ---")
    print(odds_ratios.to_string(index=False))
    print("\n")
    return odds_ratios

if __name__ == "__main__":
    os.makedirs("data/processed", exist_ok=True)
    df_orders = load_diagnostics_data()

    tier_df = analyze_unit_economics(df_orders)
    delay_df = test_delivery_delay_impact(df_orders)
    odds_df = model_repeat_purchase_drivers(df_orders)

    # Export statistical summaries for Excel Scenario Model & Power BI
    tier_df.to_csv("data/processed/unit_economics_by_tier.csv", index=False)
    delay_df.to_csv("data/processed/sla_delay_impact.csv", index=False)
    odds_df.to_csv("data/processed/churn_odds_ratios.csv", index=False)
    print("Saved processed analytical tables to data/processed/.")