# ============================================================
# test_app.py — Unit tests for app.py
#
# RUN LOCALLY:
#   pip install pytest
#   pytest test_app.py -v
#
# RUN IN JENKINS (inside Jenkinsfile):
#   sh 'pytest test_app.py -v --tb=short'
#
# WHAT WE TEST:
#   - Every endpoint returns the correct HTTP status code
#   - Response bodies contain the expected fields
#   - Error handling works correctly (404, 415, 400)
# ============================================================

import pytest
import json
from app import app


# ── Pytest Fixture ─────────────────────────────────────────
# A fixture runs before each test function that uses it.
# 'client' is Flask's built-in test client — makes HTTP calls
# without actually starting a server.

@pytest.fixture
def client():
    """
    Creates a Flask test client for each test.
    testing=True disables error catching so we see real exceptions.
    """
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client  # 'yield' means: setup → run test → teardown


# ══════════════════════════════════════════════════════════
#  TEST: GET /
# ══════════════════════════════════════════════════════════

class TestHome:

    def test_status_200(self, client):
        """Root endpoint must return HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_returns_html(self, client):
        """Root endpoint now serves index.html — must return HTML."""
        response = client.get("/")
        assert "text/html" in response.content_type

    def test_page_loads(self, client):
        """Page must have content."""
        response = client.get("/")
        assert len(response.data) > 0


# ══════════════════════════════════════════════════════════
#  TEST: GET /health
# ══════════════════════════════════════════════════════════

class TestHealth:

    def test_status_200(self, client):
        """Health endpoint must return HTTP 200 — K8s depends on this."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_healthy_status(self, client):
        """Status field must say 'healthy'."""
        data = json.loads(client.get("/health").data)
        assert data["status"] == "healthy"

    def test_has_checks(self, client):
        """Response must include checks object."""
        data = json.loads(client.get("/health").data)
        assert "checks" in data
        assert data["checks"]["app"] == "ok"


# ══════════════════════════════════════════════════════════
#  TEST: GET /info
# ══════════════════════════════════════════════════════════

class TestInfo:

    def test_status_200(self, client):
        response = client.get("/info")
        assert response.status_code == 200

    def test_has_sections(self, client):
        """Response must contain app, host, runtime, kubernetes sections."""
        data = json.loads(client.get("/info").data)
        assert "app"        in data
        assert "host"       in data
        assert "runtime"    in data
        assert "kubernetes" in data

    def test_app_section(self, client):
        data = json.loads(client.get("/info").data)
        assert data["app"]["name"] == "future-mlops-architect"


# ══════════════════════════════════════════════════════════
#  TEST: GET /api/v1/predict
# ══════════════════════════════════════════════════════════

class TestPredictGet:

    def test_status_200(self, client):
        response = client.get("/api/v1/predict")
        assert response.status_code == 200

    def test_has_prediction(self, client):
        """Response must include a prediction object."""
        data = json.loads(client.get("/api/v1/predict").data)
        assert "prediction"  in data
        assert "label"       in data["prediction"]
        assert "confidence"  in data["prediction"]
        assert "score"       in data["prediction"]

    def test_has_input(self, client):
        """Response must echo back the input."""
        data = json.loads(client.get("/api/v1/predict").data)
        assert "input" in data

    def test_valid_label(self, client):
        """Prediction label must be one of the known classes."""
        data = json.loads(client.get("/api/v1/predict").data)
        assert data["prediction"]["label"] in ["class_A", "class_B", "class_C"]

    def test_confidence_range(self, client):
        """Confidence score must be between 0 and 1."""
        data = json.loads(client.get("/api/v1/predict").data)
        conf = data["prediction"]["confidence"]
        assert 0.0 <= conf <= 1.0


# ══════════════════════════════════════════════════════════
#  TEST: POST /api/v1/predict
# ══════════════════════════════════════════════════════════

class TestPredictPost:

    def _post(self, client, payload, content_type="application/json"):
        """Helper to make POST requests."""
        return client.post(
            "/api/v1/predict",
            data=json.dumps(payload),
            content_type=content_type
        )

    def test_valid_input_200(self, client):
        """Valid JSON input must return HTTP 200."""
        response = self._post(client, {
            "feature_1": 0.5,
            "feature_2": 1.8,
            "feature_3": 0.9
        })
        assert response.status_code == 200

    def test_returns_prediction(self, client):
        """Response must include prediction with label and confidence."""
        data = json.loads(self._post(client, {
            "feature_1": 0.5,
            "feature_2": 1.8,
            "feature_3": 0.9
        }).data)
        assert data["status"] == "success"
        assert "prediction" in data
        assert "label"      in data["prediction"]

    def test_missing_field_400(self, client):
        """Missing required field must return HTTP 400."""
        response = self._post(client, {
            "feature_1": 0.5,
            "feature_2": 1.8
            # feature_3 is missing
        })
        assert response.status_code == 400

    def test_missing_field_error_message(self, client):
        """400 response must name the missing field."""
        data = json.loads(self._post(client, {
            "feature_1": 0.5
        }).data)
        assert data["status"] == "error"
        assert "feature_2"  in str(data["message"]) or \
               "feature_3"  in str(data["message"])

    def test_wrong_content_type_415(self, client):
        """Non-JSON content type must return HTTP 415."""
        response = self._post(client, {}, content_type="text/plain")
        assert response.status_code == 415

    def test_class_a_prediction(self, client):
        """High feature values should predict class_A."""
        data = json.loads(self._post(client, {
            "feature_1": 2.0,
            "feature_2": 2.0,
            "feature_3": 2.0
        }).data)
        assert data["prediction"]["label"] == "class_A"

    def test_class_c_prediction(self, client):
        """Low feature values should predict class_C."""
        data = json.loads(self._post(client, {
            "feature_1": 0.1,
            "feature_2": 0.1,
            "feature_3": 0.1
        }).data)
        assert data["prediction"]["label"] == "class_C"

    def test_invalid_feature_value_400(self, client):
        """Non-numeric feature values must return HTTP 400."""
        response = self._post(client, {
            "feature_1": "abc",   # invalid
            "feature_2": 1.0,
            "feature_3": 0.5
        })
        assert response.status_code == 400


# ══════════════════════════════════════════════════════════
#  TEST: Error Handlers
# ══════════════════════════════════════════════════════════

class TestErrorHandlers:

    def test_404_returns_json(self, client):
        """Unknown endpoints must return JSON 404, not HTML."""
        response = client.get("/this-does-not-exist")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["code"]   == 404
        assert "available"    in data

    def test_404_lists_endpoints(self, client):
        """404 response must list available endpoints."""
        data = json.loads(client.get("/wrong-path").data)
        assert "/health" in data["available"]


# ══════════════════════════════════════════════════════════
#  TEST: GET /metrics-demo
# ══════════════════════════════════════════════════════════

class TestMetricsDemo:

    def test_status_200(self, client):
        response = client.get("/metrics-demo")
        assert response.status_code == 200

    def test_has_counts(self, client):
        data = json.loads(client.get("/metrics-demo").data)
        assert "request_counts" in data
        assert "uptime_sec"     in data