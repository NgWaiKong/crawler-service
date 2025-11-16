import email
import imaplib
import poplib
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional, Protocol

from src.crawlers.base import Crawler
from src.domain.models import Email as EmailModel


class MailProtocol(Protocol):
    def close(self) -> None: ...
    def logout(self) -> None: ...
    def quit(self) -> None: ...


class TextDecoder:
    _fallbacks = ["utf-8", "gbk", "gb2312"]

    @classmethod
    def decode(cls, content: bytes, charset: Optional[str]) -> str:
        for encoding in ([charset] if charset else []) + cls._fallbacks:
            if decoded := cls._try_decode(content, encoding):
                return decoded
        return content.decode("utf-8", errors="ignore")

    @staticmethod
    def _try_decode(content: bytes, encoding: str) -> Optional[str]:
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            return None

    @classmethod
    def decode_header_text(cls, text: str) -> str:
        if not text:
            return ""
        parts = []
        for content, charset in decode_header(text):
            if isinstance(content, bytes):
                parts.append(cls.decode(content, charset))
            else:
                parts.append(str(content))
        return "".join(parts)


class MessageParser:
    def __init__(self):
        self._decoder = TextDecoder()

    def parse(self, raw: bytes) -> Optional[EmailModel]:
        try:
            msg = email.message_from_bytes(raw)
            return self._build_email(msg)
        except Exception:
            return None

    def _build_email(self, msg: Message) -> EmailModel:
        return EmailModel(
            message_id=msg.get("Message-ID", ""),
            subject=self._decoder.decode_header_text(msg.get("Subject", "")),
            from_addr=self._parse_address(msg.get("From", "")),
            to_addr=self._parse_address(msg.get("To", "")),
            date=self._parse_date(msg.get("Date", "")),
            text_body=self._extract_body(msg, "text/plain"),
            html_body=self._extract_body(msg, "text/html"),
        )

    @staticmethod
    def _parse_address(addr: str) -> str:
        return parseaddr(addr)[1] if addr else ""

    @staticmethod
    def _parse_date(date_str: str) -> str:
        if not date_str:
            return ""
        try:
            return parsedate_to_datetime(date_str).isoformat()
        except Exception:
            return date_str

    def _extract_body(self, msg: Message, content_type: str) -> str:
        parts = []
        for part in msg.walk() if msg.is_multipart() else [msg]:
            if part.get_content_type() == content_type:
                parts.append(self._decode_part(part))
        return "\n".join(filter(None, parts))

    def _decode_part(self, part: Message) -> str:
        try:
            payload = part.get_payload(decode=True)
            if not payload:
                return ""
            charset = part.get_content_charset() or "utf-8"
            return self._decoder.decode(payload, charset)
        except Exception:
            return ""


class MailConnection:
    def __init__(
        self, server: str, port: int, username: str, password: str, use_ssl: bool
    ):
        self._server = server
        self._port = port
        self._username = username
        self._password = password
        self._use_ssl = use_ssl
        self._is_imap = "imap" in server.lower()
        self._conn: Optional[MailProtocol] = None
        self.total = 0

    def connect(self) -> bool:
        try:
            self._establish()
            return True
        except Exception:
            return False

    def _establish(self) -> None:
        if self._is_imap:
            self._connect_imap()
        else:
            self._connect_pop()

    def _connect_imap(self) -> None:
        cls = imaplib.IMAP4_SSL if self._use_ssl else imaplib.IMAP4
        self._conn = cls(self._server, self._port)
        self._conn.login(self._username, self._password)
        _, data = self._conn.select("INBOX")
        self.total = int(data[0])

    def _connect_pop(self) -> None:
        cls = poplib.POP3_SSL if self._use_ssl else poplib.POP3
        self._conn = cls(self._server, self._port)
        self._conn.user(self._username)
        self._conn.pass_(self._password)
        self.total, _ = self._conn.stat()

    def disconnect(self) -> None:
        if not self._conn:
            return
        try:
            if self._is_imap:
                self._conn.close()
                self._conn.logout()
            else:
                self._conn.quit()
        except Exception:
            pass

    def fetch(self, msg_id: bytes) -> Optional[bytes]:
        try:
            if self._is_imap:
                _, data = self._conn.fetch(msg_id, "(RFC822)")
                return data[0][1]
            _, lines, _ = self._conn.retr(int(msg_id))
            return b"\r\n".join(lines)
        except Exception:
            return None


class MailCrawler(Crawler):
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
        super().__init__(database, collection)
        self._limit = limit
        self._connection = MailConnection(server, port, username, password, use_ssl)
        self._parser = MessageParser()

    def crawl(self) -> list[dict]:
        if not self._connection.connect():
            return []
        try:
            return self._fetch_all()
        finally:
            self._connection.disconnect()

    def _fetch_all(self) -> list[dict]:
        return [
            msg for msg_id in self._message_ids() if (msg := self._fetch_one(msg_id))
        ]

    def _message_ids(self) -> list[bytes]:
        if self._connection.total == 0:
            return []
        start = max(1, self._connection.total - self._limit + 1) if self._limit else 1
        return [str(i).encode() for i in range(self._connection.total, start - 1, -1)]

    def _fetch_one(self, msg_id: bytes) -> Optional[dict]:
        raw = self._connection.fetch(msg_id)
        if not raw:
            return None
        email_obj = self._parser.parse(raw)
        return email_obj.to_dict() if email_obj else None
