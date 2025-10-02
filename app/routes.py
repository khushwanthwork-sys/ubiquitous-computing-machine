from flask import Blueprint, jsonify, request, current_app
import polars as pl

bp = Blueprint("main", __name__)

def get_df():
    df = current_app.config.get("DF")
    if df is None:
        raise RuntimeError("Dataset not loaded")
    return df

@bp.route("/search", methods=["GET"])
def search():
    """
    Query params:
      - actor (matches 'cast' column)
      - director (matches 'director' column)
      - genre (matches 'listed_in' column)
    Example: /search?actor=Tom+Hanks&genre=Drama
    """
    try:
        df = get_df()

        actor = request.args.get("actor")
        director = request.args.get("director")
        genre = request.args.get("genre")

        results = df

        if actor and "cast" in df.columns:
            results = results.filter(pl.col("cast").cast(pl.Utf8).str.contains(actor, literal=False))
        if director and "director" in df.columns:
            results = results.filter(pl.col("director").str.contains(director, literal=False))
        if genre and "listed_in" in df.columns:
            results = results.filter(pl.col("listed_in").cast(pl.Utf8).str.contains(genre, literal=False))

        out = results.select(
            [col for col in ("title", "type", "release_year") if col in df.columns]
        ).head(10).to_dicts()

        return jsonify({"results": out}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
