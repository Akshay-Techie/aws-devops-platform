# ============================================================
# app.py — Future MLOps Architect | Project-04
# Flask REST API Application
#
# PURPOSE:
#   This is the application we will:
#   1. Containerize with Docker        (next step)
#   2. Push image to AWS ECR           (after Dockerfile)
#   3. Deploy to Kubernetes via Helm   (later step)
#
# ENDPOINTS:
#   GET  /                   → App identity + uptime
#   GET  /health             → Health check (K8s probes + ALB)
#   GET  /info               → Detailed system info
#   GET  /api/v1/predict     → Demo ML prediction (default input)
#   POST /api/v1/predict     → Accepts JSON, returns prediction
#   GET  /metrics-demo       → Request stats (before Prometheus)
# ============================================================

from flask import Flask, jsonify, request
from datetime import datetime
import os
import socket
import platform
import time

# ── App Initialization ─────────────────────────────────────
# __name__ tells Flask where to find templates/static files
app = Flask(__name__)

# Record when the app started — used to calculate uptime
START_TIME = time.time()

# Simple in-memory request counters
# NOTE: These reset to 0 when the pod restarts.
# In production, Prometheus handles real metrics persistence.
request_counter = {"total": 0, "predict": 0, "health": 0}


# ══════════════════════════════════════════════════════════
#  MIDDLEWARE — runs automatically before every request
# ══════════════════════════════════════════════════════════

@app.before_request
def count_requests():
    """
    Middleware: increments the total request counter.
    Flask calls this BEFORE routing to any endpoint.
    No return value — just side effects.
    """
    request_counter["total"] += 1


# ══════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════

@app.route("/", methods=["GET"])
def home():
    """
    Root endpoint — App identity and metadata.

    WHY hostname MATTERS IN KUBERNETES:
        Each pod gets a unique hostname (e.g. myapp-7d9f-xk2p).
        When 3 pods are running behind a Service, refreshing this
        endpoint shows DIFFERENT hostnames — proving load balancing works.

    EXAMPLE RESPONSE:
        {
            "app": "future-mlops-architect",
            "version": "a1b2c3d4",        <- Git commit SHA (from Jenkins)
            "hostname": "myapp-pod-abc",   <- Which K8s pod responded
            "environment": "production",
            "status": "running"
        }
    """
    return jsonify({
        "app":         "future-mlops-architect",
        "version":     os.getenv("APP_VERSION", "1.0.0"),
        "hostname":    socket.gethostname(),
        "environment": os.getenv("APP_ENV", "production"),
        "status":      "running",
        "uptime_sec":  round(time.time() - START_TIME, 2),
        "timestamp":   datetime.utcnow().isoformat() + "Z",
        "message":     "Future MLOps Architect — Project-04 Pipeline"
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint — ALWAYS returns HTTP 200 when app is alive.

    USED BY THREE DIFFERENT SYSTEMS:
        1. Kubernetes livenessProbe
               → If this fails 3x in a row, K8s RESTARTS the pod
        2. Kubernetes readinessProbe
               → If this fails, K8s STOPS sending traffic to this pod
        3. AWS ALB Target Group health check
               → If this fails, ALB marks node as unhealthy

    RULE: This endpoint should ONLY fail if the app is truly broken.
          Never add external dependencies (DB, Redis) to this check —
          use a separate /ready endpoint for dependency checks.
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
    Detailed system information endpoint.

    USEFUL FOR DEBUGGING:
        - Which image version is actually running? (check version)
        - Are K8s environment variables injected correctly?
        - Which node/pod is serving the request?
        - What Python version is inside the container?
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
            # Injected via K8s Downward API in Helm chart values.yaml
            # These will show "unknown" when running locally
            "namespace": os.getenv("K8S_NAMESPACE", "unknown"),
            "pod_name":  os.getenv("K8S_POD_NAME",  socket.gethostname()),
            "node_name": os.getenv("K8S_NODE_NAME",  "unknown"),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@app.route("/api/v1/predict", methods=["GET"])
def predict_get():
    """
    GET /api/v1/predict — Demo prediction with built-in sample input.

    In a real MLOps pipeline this endpoint would:
        1. Load model from S3 / MLflow model registry
        2. Run scaler.transform() on the input features
        3. Run model.predict() on transformed features
        4. Return prediction label + confidence score

    For Project-04 we simulate it with simple math so we don't
    need heavy ML dependencies (keeps Docker image small).

    HOW TO TEST:
        curl http://localhost:5000/api/v1/predict
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
    POST /api/v1/predict — Accepts JSON input, returns prediction.

    EXPECTED REQUEST BODY:
        {
            "feature_1": 0.5,
            "feature_2": 1.8,
            "feature_3": 0.9
        }

    RESPONSES:
        200 → Successful prediction
        400 → Missing required fields
        415 → Wrong Content-Type (must be application/json)

    HOW TO TEST:
        curl -X POST http://localhost:5000/api/v1/predict \\
             -H "Content-Type: application/json" \\
             -d '{"feature_1": 0.5, "feature_2": 1.8, "feature_3": 0.9}'
    """
    request_counter["predict"] += 1

    # ── Validate Content-Type ──────────────────────────────
    if not request.is_json:
        return jsonify({
            "status":  "error",
            "message": "Content-Type must be application/json",
            "hint":    "Add header: -H 'Content-Type: application/json'"
        }), 415

    data = request.get_json()

    # ── Validate Required Fields ───────────────────────────
    required_fields = ["feature_1", "feature_2", "feature_3"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return jsonify({
            "status":   "error",
            "message":  f"Missing required fields: {missing}",
            "required": required_fields,
            "received": list(data.keys())
        }), 400

    # ── Validate Field Types ───────────────────────────────
    for field in required_fields:
        try:
            float(data[field])
        except (TypeError, ValueError):
            return jsonify({
                "status":  "error",
                "message": f"Field '{field}' must be a number",
                "received": data[field]
            }), 400

    # ── Run Prediction ─────────────────────────────────────
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
    """
    Shows request statistics — a simplified preview of what
    Prometheus will scrape automatically once we add
    prometheus_flask_exporter in the monitoring step.

    WHAT PROMETHEUS ACTUALLY EXPOSES (format):
        http_requests_total{method="GET",endpoint="/",status="200"} 42
        http_request_duration_seconds_sum{endpoint="/health"} 0.003
    """
    return jsonify({
        "request_counts": request_counter,
        "uptime_sec":     round(time.time() - START_TIME, 2),
        "pod":            socket.gethostname(),
        "note":           "Real metrics: Prometheus scrapes /metrics endpoint"
    }), 200


# ══════════════════════════════════════════════════════════
#  ERROR HANDLERS — return JSON instead of Flask HTML pages
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
        "message": "Method not allowed for this endpoint"
    }), 405


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "status":  "error",
        "code":    500,
        "message": "Internal server error"
    }), 500


# ══════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════

def _run_prediction(features: dict) -> dict:
    """
    Simulated ML prediction function.

    REAL MLOPS VERSION WOULD:
        import mlflow
        model = mlflow.sklearn.load_model("s3://my-bucket/model/v1")
        scaler = joblib.load("scaler.pkl")
        X = scaler.transform([[f1, f2, f3]])
        label = model.predict(X)[0]
        proba = model.predict_proba(X)[0].max()
        return {"label": label, "confidence": float(proba)}

    For Project-04 we keep it dependency-free so the Docker
    image stays small and builds fast during Jenkins CI.
    """
    f1 = float(features.get("feature_1", 0))
    f2 = float(features.get("feature_2", 0))
    f3 = float(features.get("feature_3", 0))

    # Weighted sum — simulates a model score
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

    # FLASK_DEBUG=true only for local development
    # NEVER set debug=True in production — exposes interactive debugger
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    print(f"""
    ╔══════════════════════════════════════════════╗
    ║   Future MLOps Architect  —  Project-04      ║
    ║   Port:        {port}                           ║
    ║   Environment: {os.getenv('APP_ENV','production')}                ║
    ║   Version:     {os.getenv('APP_VERSION','1.0.0')}                 ║
    ║   Debug:       {debug}                         ║
    ╚══════════════════════════════════════════════╝
    Endpoints:
        GET  /                 → App info
        GET  /health           → Health check
        GET  /info             → System info
        GET  /api/v1/predict   → Demo prediction
        POST /api/v1/predict   → Custom prediction
        GET  /metrics-demo     → Request stats
    """)

    app.run(host="0.0.0.0", port=port, debug=debug)