from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Email:
    message_id: str
    subject: str
    from_addr: str
    to_addr: str
    date: str
    text_body: str
    html_body: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["_id"] = data.pop("message_id")
        return data


@dataclass
class RssArticle:
    title: str
    link: str
    published: str
    summary: str
    content: str
    author: str
    feed_title: str
    feed_url: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["_id"] = f"{self.feed_url}:{self.link}"
        return data
