"""
Legacy entry point. Prefer running from the backend directory:
  cd backend && python app.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import app  # noqa: E402, F401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
