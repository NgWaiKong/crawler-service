import pytest


@pytest.mark.asyncio
async def test_rss_crawl_endpoint(client):
    response = client.post(
        "/api/v1/rss/crawl",
        json={
            "urls": ["https://www.qbitai.com/feed", "https://wechat2rss.bestblogs.dev/feed/2d790e38f8af54c5af77fa5fed687a7c66d34c22.xml"],
            "database": "test_db",
            "collection": "test_rss",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Task accepted"
