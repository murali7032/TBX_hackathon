from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    FeedbackRequest,
)
from app.services.agent import run_chat_agent
from app.services.sessions import session_store

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session = session_store.get_or_create(body.session_id)
    try:
        return await run_chat_agent(
            db,
            session,
            body.message.strip(),
            optimize_for=body.optimize_for,
            retry=body.retry,
            previous_sql=body.previous_sql,
            previous_answer=body.previous_answer,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc


@router.post("/feedback", response_model=ChatResponse | dict)
async def feedback(body: FeedbackRequest, db: Session = Depends(get_db)):
    """Thumbs up/down. Thumbs-down regenerates with a different SQL approach."""
    session = session_store.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if body.rating == "up":
        return {
            "status": "ok",
            "rating": "up",
            "session_id": body.session_id,
            "message": "Thanks for the feedback.",
        }

    try:
        return await run_chat_agent(
            db,
            session,
            body.message.strip(),
            optimize_for=body.optimize_for,
            retry=True,
            previous_sql=body.previous_sql,
            previous_answer=body.previous_answer,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc


@router.get("/{session_id}", response_model=ChatSessionOut)
def get_session(session_id: str) -> ChatSessionOut:
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = [
        ChatHistoryMessage(role=m["role"], content=str(m.get("content") or ""))
        for m in session.messages
        if m.get("role") in {"user", "assistant"}
    ]
    return ChatSessionOut(session_id=session.session_id, messages=messages)


@router.delete("/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    if not session_store.delete(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_id": session_id}
