from flask import Blueprint, jsonify, request, current_app
import polars as pl
from functools import lru_cache

bp = Blueprint("main", __name__)

def get_df():
    df = current_app.config.get("DF")
    if df is None:
        raise RuntimeError("Dataset not loaded")
    return df

# Optional: cache the last 128 unique queries
@lru_cache(maxsize=128)
def cached_search(actor, director, genre):
    df = get_df()
    lf = df.lazy()

    if actor:
        lf = lf.filter(pl.col("cast").str.contains(actor, literal=False))
    if director:
        lf = lf.filter(pl.col("director").str.contains(director, literal=False))
    if genre:
        lf = lf.filter(pl.col("listed_in").str.contains(genre, literal=False))

    results = lf.select(["title", "type", "release_year"]).head(10).collect()
    return results.to_dicts()

@bp.route("/search", methods=["GET"])
def search():
    """
    Query parameters:
        - actor (optional)
        - director (optional)
        - genre (optional)
    Example: /search?actor=Tom+Hanks&genre=Drama
    """

    allowed_params = {"actor", "director", "genre"}
    request_params = set(request.args.keys())

    # Check for unsupported params
    invalid_params = request_params - allowed_params
    if invalid_params:
        return jsonify({
            "error": f"Unsupported query parameter(s): {', '.join(invalid_params)}"
        }), 400

    try:
        actor = request.args.get("actor")
        director = request.args.get("director")
        genre = request.args.get("genre")

        results = cached_search(actor, director, genre)
        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
