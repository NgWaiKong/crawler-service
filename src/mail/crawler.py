import imaplib
import poplib
import email
from dataclasses import dataclass, asdict
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional, Protocol, Any
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
        data = asdict(self)
        data["_id"] = data.pop("message_id")
        return data


class MailProtocol(Protocol):
    def close(self) -> None: ...
    def logout(self) -> None: ...
    def quit(self) -> None: ...


class TextDecoder:
    FALLBACK_ENCODINGS = ["utf-8", "gbk", "gb2312"]

    @classmethod
    def decode_bytes(cls, content: bytes, charset: Optional[str]) -> str:
        for encoding in [charset] + cls.FALLBACK_ENCODINGS:
            if encoding and (decoded := cls._try_decode(content, encoding)):
                return decoded
        return content.decode("utf-8", errors="ignore")

    @staticmethod
    def _try_decode(content: bytes, encoding: str) -> Optional[str]:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            return None

    @classmethod
    def decode_header(cls, header: str) -> str:
        if not header:
            return ""
        parts = [
            (
                cls.decode_bytes(content, charset)
                if isinstance(content, bytes)
                else str(content)
            )
            for content, charset in decode_header(header)
        ]
        return "".join(parts)


class MessageParser:
    def __init__(self, decoder: TextDecoder):
        self.decoder = decoder

    def parse(self, msg_data: bytes) -> Optional[Email]:
        try:
            msg = email.message_from_bytes(msg_data)
            return Email(
                message_id=msg.get("Message-ID", ""),
                subject=self.decoder.decode_header(msg.get("Subject", "")),
                from_addr=self._extract_address(msg.get("From", "")),
                to_addr=self._extract_address(msg.get("To", "")),
                date=self._parse_date(msg.get("Date", "")),
                text_body=self._extract_body(msg, "text/plain"),
                html_body=self._extract_body(msg, "text/html"),
            )
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            return None

    @staticmethod
    def _extract_address(addr_str: str) -> str:
        return parseaddr(addr_str)[1] if addr_str else ""

    @staticmethod
    def _parse_date(date_str: str) -> str:
        if not date_str:
            return ""
        try:
            return parsedate_to_datetime(date_str).isoformat()
        except Exception:
            return date_str

    def _extract_body(self, msg: Message, content_type: str) -> str:
        parts = [
            self._decode_part(part)
            for part in (msg.walk() if msg.is_multipart() else [msg])
            if part.get_content_type() == content_type
        ]
        return "\n".join(filter(None, parts))

    def _decode_part(self, part: Message) -> str:
        try:
            payload = part.get_payload(decode=True)
            if not payload:
                return ""
            charset = part.get_content_charset() or "utf-8"
            return self.decoder.decode_bytes(payload, charset)
        except Exception:
            return ""


class MailConnection:
    def __init__(
        self, server: str, port: int, username: str, password: str, use_ssl: bool
    ):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.is_imap = "imap" in server.lower()
        self.conn: Optional[MailProtocol] = None
        self.total_messages = 0

    def connect(self) -> bool:
        try:
            self._establish_connection()
            return True
        except Exception as e:
            logger.error(f"Connect failed: {e}")
            return False

    def _establish_connection(self):
        if self.is_imap:
            self._connect_imap()
        else:
            self._connect_pop()

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

    def disconnect(self):
        if not self.conn:
            return
        try:
            self._close_connection()
        except Exception as e:
            logger.error(f"Disconnect failed: {e}")

    def _close_connection(self):
        if self.is_imap:
            self.conn.close()
            self.conn.logout()
        else:
            self.conn.quit()

    def fetch_raw_message(self, msg_id: bytes) -> Optional[bytes]:
        try:
            if self.is_imap:
                _, data = self.conn.fetch(msg_id, "(RFC822)")
                return data[0][1]
            else:
                _, lines, _ = self.conn.retr(int(msg_id))
                return b"\r\n".join(lines)
        except Exception as e:
            logger.error(f"Fetch {msg_id} failed: {e}")
            return None


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
        self._database = database
        self._collection = collection
        self.limit = limit
        self.connection = MailConnection(server, port, username, password, use_ssl)
        self.parser = MessageParser(TextDecoder())

    @property
    def database_name(self) -> str:
        return self._database

    @property
    def collection_name(self) -> str:
        return self._collection

    def get_document_id(self, item: dict[str, Any]) -> str:
        return item["_id"]

    def crawl(self, **kwargs) -> list[dict[str, Any]]:
        if not self.connection.connect():
            return []
        try:
            return [
                msg
                for msg_id in self._get_message_ids()
                if (msg := self._fetch_message(msg_id))
            ]
        finally:
            self.connection.disconnect()

    def _get_message_ids(self) -> list[bytes]:
        if self.connection.total_messages == 0:
            return []
        start = (
            max(1, self.connection.total_messages - self.limit + 1) if self.limit else 1
        )
        return [
            str(i).encode()
            for i in range(self.connection.total_messages, start - 1, -1)
        ]

    def _fetch_message(self, msg_id: bytes) -> Optional[dict[str, Any]]:
        raw_data = self.connection.fetch_raw_message(msg_id)
        if not raw_data:
            return None
        email_obj = self.parser.parse(raw_data)
        return email_obj.to_dict() if email_obj else None
