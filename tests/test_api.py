import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_hotel_search_api():
    response = client.get("/api/hotels/search?city=Bengaluru")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_ride_estimates_api():
    response = client.get("/api/rides/estimates?pickup=Indiranagar&dropoff=Koramangala")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_plan_trip_api():
    payload = {
        "user_id": "user_123",
        "query": "Weekend trip to Bengaluru with luxury hotel and pool"
    }
    response = client.post("/api/trips/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "generated_plan" in data
    assert data["generated_plan"]["destination"] == "Bengaluru"
