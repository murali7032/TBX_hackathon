import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import SuggestedQuestion from "../components/chat/SuggestedQuestion";
import TbxLogo from "../components/TbxLogo";
import { backendUrl, fetchWithTimeout, API_TIMEOUT_MS } from "../api";

const fetchChat = (path, options) =>
  fetchWithTimeout(`${backendUrl}${path}`, options, API_TIMEOUT_MS);

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
    "What's the balance for HDFC accounts?",
    "Show me the math: debits by month with MoM change",
    "Is spend increasing — flag any anomalous months?",
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
        latency: data.latency || null,
        confidence: data.confidence,
        status: data.status,
        choices: data.choices || [],
        insights: data.insights || [],
        userQuestion,
        showFeedback: !(data.choices && data.choices.length > 1),
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
      const response = await fetchChat("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: trimmedQuestion,
            session_id: sessionId,
            optimize_for: optimizeFor,
          }),
        });

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
      await fetchChat("/chat/feedback", {
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
      const response = await fetchChat("/chat/feedback", {
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
        });

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
            Response profile
            <select
              value={optimizeFor}
              onChange={(e) => setOptimizeFor(e.target.value)}
              disabled={loading}
            >
              <option value="cost">Efficient</option>
              <option value="balanced">Balanced</option>
              <option value="intelligence">Precision</option>
            </select>
          </label>
        </div>

        {messages.length === 0 ? (
          <div className="chat-empty">
            <div className="chat-hero-brand">
              <TbxLogo size={56} />
              <div className="chat-hero-copy">
                <p className="chat-product-eyebrow">TBX Finance</p>
                <h1>TBX Insight</h1>
                <p className="chat-product-tagline">
                  Grounded answers across banks, accounts, and ledgers —
                  every figure traced to your data.
                </p>
              </div>
            </div>
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
                onChooseAccount={(choice) => {
                  if (choice?.follow_up) askQuestion(choice.follow_up);
                }}
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
          TBX Insight answers only from your connected ledger data. Feedback
          regenerates with an alternate SQL path when needed.
        </p>
      </div>
    </div>
  );
}

export default Chat;
