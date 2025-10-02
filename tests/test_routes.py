import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_search_actor(client):
    rv = client.get("/search?actor=Tom%20Hanks")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "results" in data

def test_search_genre(client):
    rv = client.get("/search?genre=Comedy")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "results" in data