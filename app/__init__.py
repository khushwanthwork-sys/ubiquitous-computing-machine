from flask import Flask
import polars as pl
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """
    Application factory for Flask app.
    Loads Netflix dataset once at startup using Polars.
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['JSON_SORT_KEYS'] = False
    
    # Dataset path
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                'netflix_titles.csv')
    
    try:
        logger.info(f"Loading dataset from: {dataset_path}")
        
        # Load CSV with Polars
        df = pl.read_csv(dataset_path)
        logger.info(f"✅ Loaded {len(df)} records from Netflix dataset")
        
        # CRITICAL: Cast categorical columns to UTF-8 strings at startup
        # This prevents runtime casting on every query
        df = df.with_columns([
            pl.col("cast").cast(pl.Utf8).fill_null(""),
            pl.col("director").cast(pl.Utf8).fill_null(""),
            pl.col("listed_in").cast(pl.Utf8).fill_null("")
        ])
        
        logger.info("✅ Columns cast to UTF-8 at startup")
        
        # Store DataFrame in app config
        app.config["DF"] = df
        app.config["DF_ID"] = id(df)  # For cache validation
        
        # Log basic stats
        logger.info(f"Movies: {df.filter(pl.col('type') == 'Movie').height}")
        logger.info(f"TV Shows: {df.filter(pl.col('type') == 'TV Show').height}")
        
    except FileNotFoundError:
        logger.error(f"❌ Dataset not found at: {dataset_path}")
        logger.error("Please download from: https://www.kaggle.com/datasets/shivamb/netflix-shows/data")
        raise
    except Exception as e:
        logger.error(f"❌ Failed to load dataset: {str(e)}")
        raise
    
    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)
    
    logger.info("✅ Flask app initialized successfully")
    
    return app