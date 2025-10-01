from flask import Blueprint, request, jsonify
import pandas as pd
from io import StringIO

bp = Blueprint("main", __name__)

@bp.route("/process-data", methods=["POST"])
def process_data():
    """
    Example: expects CSV in request body
    """
    try:
        csv_data = request.data.decode("utf-8")
        df = pd.read_csv(StringIO(csv_data))

        # Example operation: count rows and columns
        result = {
            "rows": df.shape[0],
            "columns": df.shape[1],
            "columns_list": df.columns.tolist()
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
