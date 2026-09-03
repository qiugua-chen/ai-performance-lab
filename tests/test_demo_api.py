from time import perf_counter

from fastapi.testclient import TestClient

from examples.demo_api.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_normal_response() -> None:
    response = client.get("/api/normal")

    assert response.status_code == 200
    assert response.json() == {
        "mode": "normal",
        "message": "request completed successfully",
    }


def test_controlled_slow_response() -> None:
    started_at = perf_counter()

    response = client.get(
        "/api/slow",
        params={"delay_ms": 100},
    )

    elapsed_ms = (perf_counter() - started_at) * 1000

    assert response.status_code == 200
    assert response.json() == {
        "mode": "slow",
        "delay_ms": 100,
    }
    assert elapsed_ms >= 80


def test_controlled_error_response() -> None:
    response = client.get(
        "/api/error",
        params={"status_code": 503},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "controlled error response",
    }


def test_rejects_excessive_delay() -> None:
    response = client.get(
        "/api/slow",
        params={"delay_ms": 5001},
    )

    assert response.status_code == 422


def test_rejects_non_error_status_code() -> None:
    response = client.get(
        "/api/error",
        params={"status_code": 200},
    )

    assert response.status_code == 422