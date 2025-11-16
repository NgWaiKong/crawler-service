import pytest


@pytest.mark.asyncio
async def test_api_mail_post_pop(client):
    test_config = {
        "server": "pop.163.com",
        "port": 995,
        "username": "17306161024@163.com",
        "password": "FHyVNNUpZjdGABGB",
        "database": "test_db",
        "collection": "test_crawler_emails",
        "limit": 2,
        "use_ssl": True,
    }
    client = client.post("/api/v1/mail/crawl", json=test_config)
    assert client.status_code == 200


@pytest.mark.asyncio
async def test_api_mail_post_imap(client):
    test_config = {
        "server": "imap.exmail.qq.com",
        "port": 993,
        "username": "zhoum@primecapital.com.cn",
        "password": "Gsfsj2025!",
        "database": "test_db",
        "collection": "test_mail",
        "limit": 2,
        "use_ssl": True,
    }
    client = client.post("/api/v1/mail/crawl", json=test_config)
    assert client.status_code == 200


@pytest.mark.asyncio
async def test_api_mail_post_imap_2(client):
    test_config = {
        "server": "imap.larksuite.com",
        "port": 993,
        "username": "stackinfo@consensusai.ai",
        "password": "JdfRMyxAjGg8cUMa",
        "database": "test_db",
        "collection": "test_mail_2",
        "limit": 2,
        "use_ssl": True,
    }
    client = client.post("/api/v1/mail/crawl", json=test_config)
    assert client.status_code == 200
