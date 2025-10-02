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

    # Optimize memory by casting likely categorical columns
    for col in ("type", "listed_in", "rating", "country"):
        if col in df.columns:
            df = df.with_columns(df[col].cast(pl.Categorical))

    print(f"[INFO] Loaded dataset: {df.height} rows, {len(df.columns)} cols")
    return df

def create_app():
    app = Flask(__name__)

    # Load dataset at startup and stash on app config
    df = init_dataset()
    app.config["DF"] = df

    # Register routes (import after df loaded to avoid circular surprises)
    from .routes import bp
    app.register_blueprint(bp)

    return app
