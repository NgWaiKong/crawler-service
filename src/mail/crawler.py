import poplib
import email
from email.message import Message
from dataclasses import dataclass
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import List, Dict, Any, Optional
import logging

from src.core.base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


@dataclass
class Email:
    message_id: str
    subject: str
    from_addr: str
    to_addr: str
    date: str
    text_body: str
    html_body: str

    def to_dict(self) -> dict:
        return {
            "_id": self.message_id,
            "subject": self.subject,
            "from_addr": self.from_addr,
            "to_addr": self.to_addr,
            "date": self.date,
            "text_body": self.text_body,
            "html_body": self.html_body,
        }


class MailCrawler(BaseCrawler):
    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str,
        database: str,
        collection: str,
        limit: Optional[int] = None,
        use_ssl: bool = True,
    ):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self._database = database
        self._collection = collection
        self.limit = limit
        self.use_ssl = use_ssl
        self.conn: Optional[poplib.POP3_SSL] = None

    @property
    def database_name(self) -> str:
        return self._database

    @property
    def collection_name(self) -> str:
        return self._collection

    def get_document_id(self, item: Dict[str, Any]) -> str:
        return item["_id"]

    def connect(self) -> bool:
        try:
            self.conn = (
                poplib.POP3_SSL(self.server, self.port)
                if self.use_ssl
                else poplib.POP3(self.server, self.port)
            )
            self.conn.user(self.username)
            self.conn.pass_(self.password)
            return True
        except Exception as e:
            logger.error(f"Connect failed: {e}")
            return False

    def disconnect(self):
        if self.conn:
            try:
                self.conn.quit()
            except Exception as e:
                logger.error(f"Disconnect failed: {e}")

    def decode_bytes(self, content: bytes, charset: Optional[str]) -> str:
        for encoding in [charset, "utf-8", "gbk", "gb2312"]:
            if not encoding:
                continue
            try:
                return content.decode(encoding)
            except:
                continue
        return content.decode("utf-8", errors="ignore")

    def decode_header(self, header: str) -> str:
        if not header:
            return ""
        result = []
        for content, charset in decode_header(header):
            if isinstance(content, bytes):
                result.append(self.decode_bytes(content, charset))
            else:
                result.append(str(content))
        return "".join(result)

    def parse_date(self, date_str: str) -> str:
        if not date_str:
            return ""
        try:
            return parsedate_to_datetime(date_str).isoformat()
        except:
            return date_str

    def extract_addr(self, addr_str: str) -> str:
        return parseaddr(addr_str)[1] if addr_str else ""

    def decode_part(self, part) -> str:
        try:
            payload = part.get_payload(decode=True)
            if not payload:
                return ""
            charset = part.get_content_charset() or "utf-8"
            return self.decode_bytes(payload, charset)
        except:
            return ""

    def extract_body(self, msg: Message, content_type: str) -> str:
        parts = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == content_type:
                    parts.append(self.decode_part(part))
        else:
            if msg.get_content_type() == content_type:
                parts.append(self.decode_part(msg))
        return "\n".join(filter(None, parts))

    def parse_message(self, msg_data: bytes) -> Optional[Email]:
        try:
            msg = email.message_from_bytes(msg_data)
            return Email(
                message_id=msg.get("Message-ID", ""),
                subject=self.decode_header(msg.get("Subject", "")),
                from_addr=self.extract_addr(msg.get("From", "")),
                to_addr=self.extract_addr(msg.get("To", "")),
                date=self.parse_date(msg.get("Date", "")),
                text_body=self.extract_body(msg, "text/plain"),
                html_body=self.extract_body(msg, "text/html"),
            )
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            return None

    def fetch_message(self, index: int) -> Optional[Dict[str, Any]]:
        try:
            _, lines, _ = self.conn.retr(index)
            email_obj = self.parse_message(b"\r\n".join(lines))
            return email_obj.to_dict() if email_obj else None
        except Exception as e:
            logger.error(f"Fetch {index} failed: {e}")
            return None

    def get_range(self, total: int) -> range:
        start = 1 if self.limit is None else max(1, total - self.limit + 1)
        return range(total, start - 1, -1)

    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        if not self.connect():
            return []
        try:
            total, _ = self.conn.stat()
            return [
                msg for i in self.get_range(total) if (msg := self.fetch_message(i))
            ]
        finally:
            self.disconnect()
