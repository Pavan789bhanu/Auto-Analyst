import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(__file__))

import models
import storage
from analyst_service import run_analysis
from config import CORS_ORIGINS, SECRET_KEY, UPLOAD_DIR

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
CORS(app, origins=CORS_ORIGINS, supports_credentials=True)
jwt = JWTManager(app)

models.init_db()
storage.ensure_dirs()


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"],
    }


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "autoanalyst-api"})


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"message": "Username, email, and password are required."}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters."}), 400
    if models.get_user_by_username(username):
        return jsonify({"message": "Username already exists."}), 400
    if models.get_user_by_email(email):
        return jsonify({"message": "Email already registered."}), 400

    user = models.create_user(username, email, password)
    token = create_access_token(identity=str(user["id"]))
    return (
        jsonify(
            {
                "message": "Account created successfully.",
                "access_token": token,
                "user": public_user(user),
            }
        ),
        201,
    )


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = models.verify_user(username, password)
    if not user:
        return jsonify({"message": "Invalid username or password."}), 401

    token = create_access_token(identity=str(user["id"]))
    return jsonify(
        {
            "access_token": token,
            "user": public_user(user),
        }
    )


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = models.get_user_by_id(user_id)
    if not user:
        return jsonify({"message": "User not found."}), 404
    stats = models.get_user_stats(user_id)
    return jsonify({"user": public_user(user), "stats": stats})


@app.route("/api/datasets", methods=["GET"])
@jwt_required()
def list_datasets():
    user_id = int(get_jwt_identity())
    datasets = models.list_datasets_for_user(user_id)
    return jsonify({"datasets": datasets})


@app.route("/api/datasets/upload", methods=["POST"])
@jwt_required()
def upload_dataset():
    import pandas as pd

    user_id = int(get_jwt_identity())
    if "file" not in request.files:
        return jsonify({"message": "No file provided."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"message": "No file selected."}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".csv"):
        return jsonify({"message": "Only CSV files are supported."}), 400

    username = models.get_user_by_id(user_id)["username"]
    file_key = f"{username}/{filename}"
    storage.save_upload(file, file_key)

    local_path = storage.get_local_path(file_key)
    try:
        dataset = pd.read_csv(local_path)
    except Exception as exc:
        storage.delete_file(file_key)
        return jsonify({"message": f"Invalid CSV file: {exc}"}), 400

    dataset_record = models.create_dataset(
        user_id=user_id,
        filename=filename,
        file_key=file_key,
        size_bytes=os.path.getsize(local_path),
        row_count=len(dataset),
        column_count=len(dataset.columns),
        columns=list(dataset.columns),
    )
    return jsonify({"message": "Dataset uploaded successfully.", "dataset": dataset_record})


@app.route("/api/analyses", methods=["GET"])
@jwt_required()
def list_analyses():
    user_id = int(get_jwt_identity())
    analyses = models.list_analyses_for_user(user_id)
    return jsonify({"analyses": analyses})


@app.route("/api/analyses", methods=["POST"])
@jwt_required()
def create_analysis():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    dataset_id = data.get("dataset_id")

    if not query:
        return jsonify({"message": "Query is required."}), 400
    if not dataset_id:
        return jsonify({"message": "dataset_id is required."}), 400

    dataset = models.get_dataset_by_id(int(dataset_id))
    if not dataset or dataset["user_id"] != user_id:
        return jsonify({"message": "Dataset not found."}), 404

    analysis = models.create_analysis(user_id, dataset["id"], query)

    try:
        local_path = storage.get_local_path(dataset["file_key"])
        result = run_analysis(local_path, query)
        analysis = models.update_analysis(
            analysis["id"],
            status="completed",
            plan=result.get("plan"),
            plan_desc=result.get("plan_desc"),
            output=result.get("output"),
            agent_outputs=result.get("agent_outputs"),
        )
        analysis["dataset_preview"] = result.get("dataset_preview")
    except Exception as exc:
        analysis = models.update_analysis(
            analysis["id"],
            status="failed",
            error_message=str(exc),
        )
        return jsonify({"message": "Analysis failed.", "analysis": analysis}), 500

    return jsonify({"message": "Analysis completed.", "analysis": analysis})


@app.route("/api/analyses/<int:analysis_id>", methods=["GET"])
@jwt_required()
def get_analysis(analysis_id: int):
    user_id = int(get_jwt_identity())
    analysis = models.get_analysis_by_id(analysis_id)
    if not analysis or analysis["user_id"] != user_id:
        return jsonify({"message": "Analysis not found."}), 404
    return jsonify({"analysis": analysis})


# Legacy routes for backward compatibility
@app.route("/register", methods=["POST"])
def legacy_register():
    return register()


@app.route("/login", methods=["POST"])
def legacy_login():
    return login()


@app.route("/upload", methods=["POST"])
@jwt_required()
def legacy_upload():
    return upload_dataset()


@app.route("/query", methods=["POST"])
@jwt_required()
def legacy_query():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    file_key = data.get("file_key")

    if not query or not file_key:
        return jsonify({"message": "query and file_key are required."}), 400

    datasets = models.list_datasets_for_user(user_id)
    dataset = next((item for item in datasets if item["file_key"] == file_key), None)
    if not dataset:
        return jsonify({"message": "Dataset not found."}), 404

    with app.test_request_context(
        json={"query": query, "dataset_id": dataset["id"]},
        headers=request.headers,
    ):
        return create_analysis()


@app.route("/results", methods=["GET"])
@jwt_required()
def legacy_results():
    user_id = int(get_jwt_identity())
    analyses = models.list_analyses_for_user(user_id)
    legacy = [
        {
            "output": item.get("output"),
            "agent_outputs": item.get("agent_outputs"),
            "query": item.get("query"),
            "status": item.get("status"),
        }
        for item in analyses
    ]
    return jsonify(legacy)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
