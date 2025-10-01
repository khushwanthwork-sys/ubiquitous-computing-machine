import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_process_data(client):
    csv_data = "name,age\nAlice,30\nBob,25"
    response = client.post(
        "/process-data",
        data=csv_data,
        content_type="text/csv"
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["rows"] == 2
    assert data["columns"] == 2
    assert data["columns_list"] == ["name", "age"]
