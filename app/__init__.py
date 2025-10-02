import os
import polars as pl
from flask import Flask

DATA_FILE = "netflix_titles.csv"

def init_dataset():
    """
    Load the CSV into a Polars DataFrame and return it.
    Raises FileNotFoundError if CSV not present.
    """
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Dataset {DATA_FILE} not found. Please place netflix_titles.csv in the project root."
        )

    print("[INFO] Loading dataset with Polars...")
    df = pl.read_csv(DATA_FILE)

    # Cast commonly searched columns to Utf8 once
    for col in ("cast", "director", "listed_in"):
        if col in df.columns:
            df = df.with_columns(df[col].cast(pl.Utf8))

    print(f"[INFO] Loaded dataset: {df.height} rows, {len(df.columns)} cols")
    return df

def create_app():
    app = Flask(__name__)

    # Load dataset at startup
    df = init_dataset()
    app.config["DF"] = df

    # Blueprint for routes
    from .routes import bp
    app.register_blueprint(bp)

    return app
