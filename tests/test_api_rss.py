import pytest


@pytest.mark.asyncio
async def test_rss_crawl_endpoint(client):
    response = client.post(
        "/rss/crawl",
        json={
            "rss_url": "https://www.qbitai.com/feed",
            "database": "test_db",
            "collection": "test_rss",
            "limit": 2,
            "fetch_full_content": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Task accepted"