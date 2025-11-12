import imaplib
import poplib
import email
from email.message import Message
from dataclasses import dataclass
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from typing import List, Dict, Any, Optional, Union
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
        self.is_imap = "imap" in server.lower()
        self.conn: Optional[Union[imaplib.IMAP4_SSL, poplib.POP3_SSL]] = None
        self.total_messages = 0

    @property
    def database_name(self) -> str:
        return self._database

    @property
    def collection_name(self) -> str:
        return self._collection

    def get_document_id(self, item: Dict[str, Any]) -> str:
        return item["_id"]

    def _connect_imap(self):
        cls = imaplib.IMAP4_SSL if self.use_ssl else imaplib.IMAP4
        self.conn = cls(self.server, self.port)
        self.conn.login(self.username, self.password)
        _, data = self.conn.select("INBOX")
        self.total_messages = int(data[0])

    def _connect_pop(self):
        cls = poplib.POP3_SSL if self.use_ssl else poplib.POP3
        self.conn = cls(self.server, self.port)
        self.conn.user(self.username)
        self.conn.pass_(self.password)
        self.total_messages, _ = self.conn.stat()

    def connect(self) -> bool:
        try:
            self._connect_imap() if self.is_imap else self._connect_pop()
            return True
        except Exception as e:
            logger.error(f"Connect failed: {e}")
            return False

    def disconnect(self):
        if not self.conn:
            return
        try:
            if self.is_imap:
                self.conn.close()
                self.conn.logout()
            else:
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

    def fetch_message(self, msg_id: bytes) -> Optional[Dict[str, Any]]:
        try:
            if self.is_imap:
                _, data = self.conn.fetch(msg_id, "(RFC822)")
                email_obj = self.parse_message(data[0][1])
            else:
                _, lines, _ = self.conn.retr(int(msg_id))
                email_obj = self.parse_message(b"\r\n".join(lines))
            return email_obj.to_dict() if email_obj else None
        except Exception as e:
            logger.error(f"Fetch {msg_id} failed: {e}")
            return None

    def get_message_ids(self) -> List[bytes]:
        if self.total_messages == 0:
            return []
        start = max(1, self.total_messages - self.limit + 1) if self.limit else 1
        end = self.total_messages
        return [str(i).encode() for i in range(end, start - 1, -1)]

    def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        if not self.connect():
            return []
        try:
            return [
                msg for msg_id in self.get_message_ids()
                if (msg := self.fetch_message(msg_id))
            ]
        finally:
            self.disconnect()
