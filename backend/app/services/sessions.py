from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass
class ChatSession:
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    last_evidence: dict[str, Any] | None = None


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ChatSession] = {}
        self._lock = Lock()

    def create(self) -> ChatSession:
        session = ChatSession(session_id=str(uuid4()))
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> ChatSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> ChatSession:
        if session_id:
            existing = self.get(session_id)
            if existing is not None:
                return existing
        return self.create()

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def append_messages(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            session.messages.extend(messages)

    def set_evidence(self, session_id: str, evidence: dict[str, Any]) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                session.last_evidence = evidence


session_store = SessionStore()
