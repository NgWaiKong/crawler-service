import pytest


@pytest.mark.asyncio
async def test_api_mail_post_pop(client):
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


@pytest.mark.asyncio
async def test_api_mail_post_imap(client):
    test_config = {
        "mail_server": "imap.exmail.qq.com",
        "mail_port": 993,
        "username": "zhoum@primecapital.com.cn",
        "password": "Gsfsj2025!",
        "database": "finance_data",
        "collection": "mail",
        "limit": 12,
        "use_ssl": True,
    }
    client = client.post("/mail/crawl", json=test_config)
    assert client.status_code == 200




@pytest.mark.asyncio
async def test_api_mail_post_imap_2(client):
    test_config = {
        "mail_server": "imap.larksuite.com",
        "mail_port": 993,
        "username": "stackinfo@consensusai.ai",
        "password": "JdfRMyxAjGg8cUMa",
        "database": "finance_data",
        "collection": "mail_2",
        "limit": 12,
        "use_ssl": True,
    }
    client = client.post("/mail/crawl", json=test_config)
    assert client.status_code == 200
