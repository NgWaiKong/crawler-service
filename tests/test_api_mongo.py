import pytest


@pytest.mark.asyncio
async def test_mongo_crawl_endpoint(client):
    response = client.post(
        "/api/v1/mongo/crawl",
        json={
            "source_uri": "mongodb://consensus:consensus_2025@52.237.81.54:27017?authSource=admin",
            "source_database": "crawl_data",
            "source_collection": "crawled_meritco",
            "target_database": "test_db",
            "target_collection": "test_crawled_meritco",
            "limit": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Task accepted"

