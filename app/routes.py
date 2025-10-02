from flask import Blueprint, jsonify, request, current_app
import polars as pl
from functools import lru_cache
import logging
from datetime import datetime

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)


def get_df():
    """Retrieve the loaded DataFrame from app config."""
    df = current_app.config.get("DF")
    if df is None:
        raise RuntimeError("Dataset not loaded. Check app initialization.")
    return df


def validate_search_param(value, param_name, max_length=100):
    """Validate search parameters."""
    if not value:
        return None
    
    value = value.strip()
    
    if not value:
        raise ValueError(f"{param_name} cannot be empty")
    
    if len(value) > max_length:
        raise ValueError(f"{param_name} exceeds maximum length of {max_length} characters")
    
    return value


def validate_pagination(page, limit):
    """Validate pagination parameters."""
    try:
        page = int(page) if page else 1
        limit = int(limit) if limit else 20
    except ValueError:
        raise ValueError("Page and limit must be integers")
    
    if page < 1:
        raise ValueError("Page must be >= 1")
    
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
    
    return page, limit


# Cache with DataFrame ID to ensure cache validity
@lru_cache(maxsize=256)
def search_with_filters(actor, director, genre, page, limit, df_id):
    """
    Execute search query with caching.
    df_id ensures cache is invalidated if DataFrame changes.
    """
    df = get_df()
    lf = df.lazy()
    
    # Apply filters (case-insensitive)
    if actor:
        lf = lf.filter(
            pl.col("cast").str.to_lowercase().str.contains(actor.lower(), literal=False)
        )
    
    if director:
        lf = lf.filter(
            pl.col("director").str.to_lowercase().str.contains(director.lower(), literal=False)
        )
    
    if genre:
        lf = lf.filter(
            pl.col("listed_in").str.to_lowercase().str.contains(genre.lower(), literal=False)
        )
    
    # Get total count
    total = lf.select(pl.len()).collect()[0, 0]
    
    # Apply pagination
    offset = (page - 1) * limit
    results = lf.select([
        "title", 
        "type", 
        "release_year",
        "director",
        "cast",
        "listed_in",
        "description"
    ]).slice(offset, limit).collect()
    
    return {
        "results": results.to_dicts(),
        "total": int(total),
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }


@bp.route("/", methods=["GET"])
def home():
    """API information endpoint."""
    return jsonify({
        "name": "Netflix Search API",
        "version": "1.0",
        "endpoints": {
            "/search": "Search Netflix titles",
            "/stats": "Get dataset statistics",
            "/metrics": "Get cache metrics",
            "/health": "Health check"
        }
    })


@bp.route("/search", methods=["GET"])
def search():
    """
    Search Netflix titles by actor, director, or genre.
    
    Query parameters:
        - actor (optional): Search by actor name
        - director (optional): Search by director name
        - genre (optional): Search by genre/category
        - page (optional, default=1): Page number
        - limit (optional, default=20, max=100): Results per page
    
    Example: /search?actor=Tom+Hanks&genre=Drama&page=1&limit=20
    """
    try:
        # Validate allowed parameters
        allowed_params = {"actor", "director", "genre", "page", "limit"}
        request_params = set(request.args.keys())
        invalid_params = request_params - allowed_params
        
        if invalid_params:
            return jsonify({
                "error": f"Unsupported query parameter(s): {', '.join(invalid_params)}",
                "allowed_params": list(allowed_params)
            }), 400
        
        # Check if at least one search parameter is provided
        search_params = {"actor", "director", "genre"}
        if not any(request.args.get(p) for p in search_params):
            return jsonify({
                "error": "At least one search parameter required (actor, director, or genre)"
            }), 400
        
        # Validate search parameters
        actor = validate_search_param(request.args.get("actor"), "actor")
        director = validate_search_param(request.args.get("director"), "director")
        genre = validate_search_param(request.args.get("genre"), "genre")
        
        # Validate pagination
        page, limit = validate_pagination(
            request.args.get("page"),
            request.args.get("limit")
        )
        
        # Get DataFrame ID for cache
        df_id = current_app.config.get("DF_ID")
        
        # Execute cached search
        result = search_with_filters(actor, director, genre, page, limit, df_id)
        
        logger.info(f"Search: actor={actor}, director={director}, genre={genre}, "
                   f"page={page}, limit={limit}, results={result['total']}")
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
    except RuntimeError as e:
        logger.error(f"Dataset error: {str(e)}")
        return jsonify({"error": "Dataset unavailable"}), 503
    
    except Exception as e:
        logger.exception("Unexpected error in search endpoint")
        return jsonify({
            "error": "Internal server error. Please try again later."
        }), 500


@bp.route("/stats", methods=["GET"])
def stats():
    """Get dataset statistics."""
    try:
        df = get_df()
        
        stats_data = {
            "total_titles": len(df),
            "movies": int(df.filter(pl.col("type") == "Movie").height),
            "tv_shows": int(df.filter(pl.col("type") == "TV Show").height),
            "year_range": {
                "min": int(df["release_year"].min()),
                "max": int(df["release_year"].max())
            },
            "top_genres": df.select("listed_in")
                .to_series()
                .str.split(", ")
                .explode()
                .value_counts()
                .head(10)
                .to_dicts()
        }
        
        return jsonify(stats_data), 200
        
    except Exception as e:
        logger.exception("Error in stats endpoint")
        return jsonify({"error": "Failed to retrieve statistics"}), 500


@bp.route("/metrics", methods=["GET"])
def metrics():
    """Get cache performance metrics."""
    try:
        cache_info = search_with_filters.cache_info()
        
        total_requests = cache_info.hits + cache_info.misses
        hit_rate = cache_info.hits / total_requests if total_requests > 0 else 0
        
        return jsonify({
            "cache": {
                "hits": cache_info.hits,
                "misses": cache_info.misses,
                "size": cache_info.currsize,
                "maxsize": cache_info.maxsize,
                "hit_rate": round(hit_rate, 3),
                "hit_rate_percent": f"{round(hit_rate * 100, 1)}%"
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.exception("Error in metrics endpoint")
        return jsonify({"error": "Failed to retrieve metrics"}), 500


@bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    try:
        df = get_df()
        return jsonify({
            "status": "healthy",
            "dataset_loaded": True,
            "records_count": len(df),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "dataset_loaded": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503