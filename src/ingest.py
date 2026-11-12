import os
import glob
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

USER = os.getenv("DB_USER")
PASS = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
DB = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASS}@{HOST}:{PORT}/{DB}"
engine = create_engine(DATABASE_URL, echo=False)

TABLE_FILE_MAP = {
    "staging.customers": "olist_customers_dataset.csv",
    "staging.orders": "olist_orders_dataset.csv",
    "staging.order_items": "olist_order_items_dataset.csv",
    "staging.order_payments": "olist_order_payments_dataset.csv",
    "staging.products": "olist_products_dataset.csv",
    "staging.order_reviews": "olist_order_reviews_dataset.csv"
}

TIMESTAMP_COLS = {
    "staging.orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ],
    "staging.order_items": ["shipping_limit_date"],
    "staging.order_reviews": ["review_creation_date", "review_answer_timestamp"]
}

def clean_and_ingest(raw_data_dir="data/raw"):
    with engine.connect() as conn:
        for table, file_name in TABLE_FILE_MAP.items():
            schema, table_name = table.split(".")
            file_path = os.path.join(raw_data_dir, file_name)
            
            if not os.path.exists(file_path):
                logging.warning(f"File not found: {file_path}. Skipping...")
                continue
            
            logging.info(f"Loading {file_name} into {table}...")
            df = pd.read_csv(file_path)
            
            # Fix Kaggle's raw header typos in products dataset
            if table == "staging.products":
                df = df.rename(columns={
                    "product_name_lenght": "product_name_length",
                    "product_description_lenght": "product_description_length"
                })

            # Convert datetime columns
            if table in TIMESTAMP_COLS:
                for col in TIMESTAMP_COLS[table]:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors="coerce")

            # Basic deduplication for primary key tables
            if table == "staging.customers":
                df = df.drop_duplicates(subset=["customer_id"])
            elif table == "staging.orders":
                df = df.drop_duplicates(subset=["order_id"])
            elif table == "staging.products":
                df = df.drop_duplicates(subset=["product_id"])
            
            # Truncate staging table before loading
            conn.execute(text(f"TRUNCATE TABLE {schema}.{table_name} CASCADE;"))
            conn.commit()

            # Batch insert using pandas
            df.to_sql(
                name=table_name,
                con=engine,
                schema=schema,
                if_exists="append",
                index=False,
                chunksize=5000,
                method="multi"
            )
            logging.info(f"Successfully loaded {len(df):,} rows into {table}.")

if __name__ == "__main__":
    clean_and_ingest()