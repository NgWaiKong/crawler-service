import pytest


@pytest.mark.asyncio
async def test_api_mail_post(client):
    test_config = {
        "mail_server": "pop.163.com",
        "mail_port": 995,
        "username": "17306161024@163.com",
        "password": "FHyVNNUpZjdGABGB",
        "database": "test_crawler",
        "collection": "test_emails",
        "limit": 100,
        "use_ssl": True,
    }
    client = client.post("/mail/crawl", json=test_config)
    assert client.status_code == 200
