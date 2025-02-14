from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import boto3
import pandas as pd
import json
import openai
import dspy
import os
import numpy as np
from data_analyst_system import DataAnalyst

def get_secret_key():
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("SECRET_KEY environment variable is not set.")
    return secret_key

def check_openai_api():
    OPENAI_KEY = os.getenv('OPENAI_API_KEY')  # API key is passed via environment variable
    if not OPENAI_KEY:
        raise ValueError("API Key not set. Please set the 'OPENAI_API_KEY' environment variable.")
    openai.api_key = OPENAI_KEY
    openai_model = dspy.OpenAI(model='gpt-3.5-turbo', api_key=OPENAI_KEY)
    dspy.settings.configure(lm=openai_model)
    

app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = get_secret_key()
jwt = JWTManager(app)

# AWS Configuration
s3 = boto3.client("s3")
sqs = boto3.client("sqs")
BUCKET_NAME = 'auto-data-analyst'
QUEUE_URL = "https://sqs.ap-southeast-2.amazonaws.com/879381271395/processing-queue.fifo"  


# Dummy user database
users = {"admin": "password123"}

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username in users:
        return jsonify({"message": "User already exists"}), 400

    users[username] = password
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username not in users or users[username] != password:
        return jsonify({"message": "Invalid username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify({"access_token": access_token}), 200

@app.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    current_user = get_jwt_identity()
    try:
        file = request.files["file"]
        file_key = f"{current_user}/{file.filename}"

        s3.upload_fileobj(file, BUCKET_NAME, file_key)

        return jsonify({"message": "File uploaded successfully!", "file_key": file_key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/query", methods=["POST"])
@jwt_required()
def submit_query():
    current_user = get_jwt_identity()
    query_data = request.json
    query = query_data.get("query")
    file_key = query_data.get("file_key")

    try:
        dataset_path = f"/tmp/{file_key.split('/')[-1]}"
        s3.download_file(BUCKET_NAME, file_key, dataset_path)

        dataset = pd.read_csv(dataset_path)
        chunk_size = 50
        chunks = np.array_split(dataset, len(dataset) // chunk_size + 1)

        output, agent_outputs = DataAnalyst.forward(chunks[0], query)

        result_key = f"{current_user}/processed-results/{file_key.split('/')[-1].replace('.csv', '_result.json')}"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=result_key,
            Body=json.dumps({"output": output, "agent_outputs": agent_outputs})
        )

        return jsonify({"message": "Query processed successfully!", "result_key": result_key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/results", methods=["GET"])
@jwt_required()
def get_results():
    current_user = get_jwt_identity()
    prefix = f"{current_user}/processed-results/"

    try:
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

        results = []
        for obj in objects.get("Contents", []):
            key = obj["Key"]
            result_data = s3.get_object(Bucket=BUCKET_NAME, Key=key)["Body"].read()
            results.append(json.loads(result_data))

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    check_openai_api()
    app.run(debug=True)