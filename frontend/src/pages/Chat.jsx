import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import SuggestedQuestion from "../components/chat/SuggestedQuestion";

const backendUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const fetchWithTimeout = async (url, options = {}, timeout = 120000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
};

function findLastUserQuestion(messages, beforeIndex) {
  for (let i = beforeIndex - 1; i >= 0; i -= 1) {
    if (messages[i]?.role === "user") return messages[i].text;
  }
  return "";
}

function Chat() {
  const location = useLocation();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [optimizeFor, setOptimizeFor] = useState("balanced");

  const suggestedQuestions = [
    "List all banks",
    "Show HDFC accounts and balances",
    "Total debits by month — is spend increasing?",
    "Find transaction with ref HDFCH01078329532",
    "Which transactions are still unreconciled?",
  ];

  useEffect(() => {
    if (location.state?.reset) {
      setMessages([]);
      setSessionId(null);
      setQuestion("");
    }
  }, [location.state?.reset]);

  const appendAssistant = (data, userQuestion, extras = {}) => {
    const assistantText =
      typeof data.message === "string"
        ? data.message
        : typeof data.answer === "string"
          ? data.answer
          : "";

    setMessages((previous) => [
      ...previous,
      {
        role: "assistant",
        text: assistantText,
        type: typeof data.type === "string" ? data.type : "text",
        data: data.data && typeof data.data === "object" ? data.data : null,
        evidence: data.evidence || null,
        tool_trace: data.tool_trace || [],
        confidence: data.confidence,
        status: data.status,
        userQuestion,
        showFeedback: true,
        feedback: null,
        retried: Boolean(data.retried),
        ...extras,
      },
    ]);
  };

  const askQuestion = async (text = question) => {
    const trimmedQuestion = text.trim();
    if (!trimmedQuestion || loading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", text: trimmedQuestion },
    ]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetchWithTimeout(
        `${backendUrl}/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: trimmedQuestion,
            session_id: sessionId,
            optimize_for: optimizeFor,
          }),
        },
        120000
      );

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || `Backend returned ${response.status}`);
      }

      const data = await response.json();
      if (data.session_id) setSessionId(data.session_id);
      appendAssistant(data, trimmedQuestion);
    } catch (error) {
      let errorMessage =
        "I'm unable to reach the finance assistant right now.";
      if (error.name === "AbortError") {
        errorMessage =
          "The finance assistant took too long to respond. Please try again.";
      } else if (error.message) {
        errorMessage = error.message;
      }
      setMessages((previous) => [
        ...previous,
        { role: "assistant", text: errorMessage, type: "text", data: null },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleThumbsUp = async (index) => {
    const msg = messages[index];
    if (!msg || !sessionId) return;
    setMessages((prev) =>
      prev.map((m, i) => (i === index ? { ...m, feedback: "up" } : m))
    );
    try {
      await fetch(`${backendUrl}/chat/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          rating: "up",
          message: msg.userQuestion || findLastUserQuestion(messages, index) || "ok",
        }),
      });
    } catch {
      // feedback is best-effort
    }
  };

  const handleThumbsDown = async (index) => {
    const msg = messages[index];
    if (!msg || loading) return;
    const originalQuestion =
      msg.userQuestion || findLastUserQuestion(messages, index);
    if (!originalQuestion) return;

    setMessages((prev) =>
      prev.map((m, i) => (i === index ? { ...m, feedback: "down", showFeedback: false } : m))
    );
    setLoading(true);

    try {
      const response = await fetchWithTimeout(
        `${backendUrl}/chat/feedback`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            rating: "down",
            message: originalQuestion,
            previous_sql: msg.evidence?.sql || null,
            previous_answer: msg.text || null,
            optimize_for: optimizeFor,
          }),
        },
        120000
      );

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || `Backend returned ${response.status}`);
      }

      const data = await response.json();
      if (data.session_id) setSessionId(data.session_id);
      // thumbs-up ack returns {status, message} without evidence
      if (data.answer || data.evidence) {
        appendAssistant(data, originalQuestion, { retried: true });
      }
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: error.message || "Retry failed. Please try again.",
          type: "text",
          data: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-container">
        <div className="chat-toolbar">
          <label className="optimize-label">
            Model mode
            <select
              value={optimizeFor}
              onChange={(e) => setOptimizeFor(e.target.value)}
              disabled={loading}
            >
              <option value="cost">cost (gemini-3.5-flash-lite)</option>
              <option value="balanced">balanced (gemini-3.5-flash)</option>
              <option value="intelligence">intelligence (gemini-3.5-flash)</option>
            </select>
          </label>
        </div>

        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-logo">✦</div>
            <h1>How can I help?</h1>
            <p>Ask about banks, accounts, balances, and transactions.</p>
            <div className="suggested-questions">
              {suggestedQuestions.map((suggestedQuestion) => (
                <SuggestedQuestion
                  key={suggestedQuestion}
                  onClick={() => askQuestion(suggestedQuestion)}
                >
                  {suggestedQuestion}
                </SuggestedQuestion>
              ))}
            </div>
          </div>
        ) : (
          <div className="chat-messages">
            {messages.map((message, index) => (
              <ChatMessage
                key={index}
                message={message}
                feedbackDisabled={loading}
                onThumbsUp={() => handleThumbsUp(index)}
                onThumbsDown={() => handleThumbsDown(index)}
              />
            ))}
            {loading && (
              <ChatMessage
                message={{ role: "assistant", text: "", type: "text", data: null }}
              >
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </ChatMessage>
            )}
          </div>
        )}

        <ChatInput
          value={question}
          onChange={setQuestion}
          onSubmit={askQuestion}
          loading={loading}
        />

        <p className="chat-disclaimer">
          Answers are grounded in the finance Postgres dataset via Gemini tools.
          Use 👎 to regenerate with a different SQL query.
        </p>
      </div>
    </div>
  );
}

export default Chat;
