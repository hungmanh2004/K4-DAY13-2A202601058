from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware import CorrelationIdMiddleware


def _client() -> TestClient:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/")
    async def root() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


def test_valid_correlation_id_is_propagated() -> None:
    with _client() as client:
        response = client.get("/", headers={"x-request-id": "client-request_01"})

    assert response.headers["x-request-id"] == "client-request_01"


def test_invalid_correlation_id_is_replaced() -> None:
    with _client() as client:
        response = client.get("/", headers={"x-request-id": "invalid id with spaces"})

    generated = response.headers["x-request-id"]
    assert generated.startswith("req-")
    assert len(generated) == 12
