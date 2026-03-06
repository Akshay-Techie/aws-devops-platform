# ============================================================
# app.py — Future MLOps Architect | Project-04
# Flask app that serves:
#   /              → Beautiful futuristic website (index.html)
#   /health        → Health check (K8s probes + ALB)
#   /info          → System info
#   /api/v1/predict  → ML prediction endpoint (GET + POST)
#   /metrics-demo  → Request stats
# ============================================================

from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import os
import socket
import platform
import time

# ── App Initialization ─────────────────────────────────────
# template_folder='.' tells Flask to look for HTML files
# in the same directory as app.py
app = Flask(__name__, template_folder='.')

START_TIME = time.time()

request_counter = {"total": 0, "predict": 0, "health": 0}


# ══════════════════════════════════════════════════════════
#  MIDDLEWARE
# ══════════════════════════════════════════════════════════

@app.before_request
def count_requests():
    request_counter["total"] += 1


# ══════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════

@app.route("/", methods=["GET"])
def home():
    """
    Root route — serves the futuristic index.html website.

    send_from_directory() safely serves a file from a directory.
    '.' means current directory (same folder as app.py).
    This is how Flask serves static HTML files.

    When Docker container runs and you open localhost:5000
    you will see the full animated website.
    """
    return send_from_directory('.', 'index.html')


@app.route("/health", methods=["GET"])
def health():
    """
    Health check — used by:
      - Kubernetes livenessProbe  (restart pod if fails)
      - Kubernetes readinessProbe (remove from service if fails)
      - AWS ALB Target Group      (stop traffic if fails)
      - Jenkins smoke test        (validate deployment)
    """
    request_counter["health"] += 1

    return jsonify({
        "status":    "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "app":        "ok",
            "uptime_sec": round(time.time() - START_TIME, 2)
        }
    }), 200


@app.route("/info", methods=["GET"])
def info():
    """
    System info — useful for debugging in Kubernetes.
    Shows which pod, node, version is serving the request.
    """
    return jsonify({
        "app": {
            "name":        "future-mlops-architect",
            "version":     os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("APP_ENV", "production"),
            "port":        os.getenv("PORT", "5000"),
            "model_name":  os.getenv("MODEL_NAME", "mlops-demo-model"),
            "model_ver":   os.getenv("MODEL_VERSION", "v1.0"),
        },
        "host": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "python":   platform.python_version(),
            "arch":     platform.machine(),
        },
        "runtime": {
            "uptime_sec":       round(time.time() - START_TIME, 2),
            "requests_total":   request_counter["total"],
            "requests_predict": request_counter["predict"],
            "requests_health":  request_counter["health"],
        },
        "kubernetes": {
            "namespace": os.getenv("K8S_NAMESPACE", "unknown"),
            "pod_name":  os.getenv("K8S_POD_NAME",  socket.gethostname()),
            "node_name": os.getenv("K8S_NODE_NAME",  "unknown"),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/api/v1/predict", methods=["GET"])
def predict_get():
    """
    GET prediction with default sample input.
    """
    request_counter["predict"] += 1

    sample_input = {"feature_1": 0.75, "feature_2": 1.20, "feature_3": 0.33}
    prediction   = _run_prediction(sample_input)

    return jsonify({
        "status":     "success",
        "endpoint":   "GET /api/v1/predict",
        "input":      sample_input,
        "prediction": prediction,
        "model": {
            "name":    os.getenv("MODEL_NAME",    "mlops-demo-model"),
            "version": os.getenv("MODEL_VERSION", "v1.0"),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/api/v1/predict", methods=["POST"])
def predict_post():
    """
    POST prediction — accepts JSON body with feature values.

    TEST WITH:
        curl -X POST http://localhost:5000/api/v1/predict
             -H "Content-Type: application/json"
             -d '{"feature_1": 0.5, "feature_2": 1.8, "feature_3": 0.9}'
    """
    request_counter["predict"] += 1

    if not request.is_json:
        return jsonify({
            "status":  "error",
            "message": "Content-Type must be application/json"
        }), 415

    data = request.get_json()

    required_fields = ["feature_1", "feature_2", "feature_3"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return jsonify({
            "status":   "error",
            "message":  f"Missing required fields: {missing}",
            "required": required_fields,
            "received": list(data.keys())
        }), 400

    for field in required_fields:
        try:
            float(data[field])
        except (TypeError, ValueError):
            return jsonify({
                "status":  "error",
                "message": f"Field '{field}' must be a number"
            }), 400

    prediction = _run_prediction(data)

    return jsonify({
        "status":     "success",
        "endpoint":   "POST /api/v1/predict",
        "input":      data,
        "prediction": prediction,
        "model": {
            "name":    os.getenv("MODEL_NAME",    "mlops-demo-model"),
            "version": os.getenv("MODEL_VERSION", "v1.0"),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/metrics-demo", methods=["GET"])
def metrics_demo():
    return jsonify({
        "request_counts": request_counter,
        "uptime_sec":     round(time.time() - START_TIME, 2),
        "pod":            socket.gethostname(),
        "note":           "Real metrics: Prometheus scrapes /metrics endpoint"
    }), 200


# ══════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status":    "error",
        "code":      404,
        "message":   "Endpoint not found",
        "available": ["/", "/health", "/info",
                      "/api/v1/predict", "/metrics-demo"]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "status":  "error",
        "code":    405,
        "message": "Method not allowed"
    }), 405


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "status":  "error",
        "code":    500,
        "message": "Internal server error"
    }), 500


# ══════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════

def _run_prediction(features: dict) -> dict:
    f1 = float(features.get("feature_1", 0))
    f2 = float(features.get("feature_2", 0))
    f3 = float(features.get("feature_3", 0))

    score = (f1 * 0.40) + (f2 * 0.35) + (f3 * 0.25)

    if score > 1.0:
        label      = "class_A"
        confidence = min(0.97, round(score / 2, 3))
    elif score > 0.5:
        label      = "class_B"
        confidence = round(0.50 + score * 0.20, 3)
    else:
        label      = "class_C"
        confidence = round(0.30 + score * 0.30, 3)

    return {
        "label":      label,
        "confidence": confidence,
        "score":      round(score, 4)
    }


# ══════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    print(f"""
    ╔══════════════════════════════════════════════╗
    ║   Future MLOps Architect  —  Project-04      ║
    ║   Port:        {port}                           ║
    ║   Environment: {os.getenv('APP_ENV','production')}                ║
    ║   Version:     {os.getenv('APP_VERSION','1.0.0')}                 ║
    ╚══════════════════════════════════════════════╝
    Endpoints:
        GET  /                 → Website (index.html)
        GET  /health           → Health check
        GET  /info             → System info
        GET  /api/v1/predict   → Demo prediction
        POST /api/v1/predict   → Custom prediction
        GET  /metrics-demo     → Request stats
    """)

    app.run(host="0.0.0.0", port=port, debug=debug)