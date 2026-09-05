function ChatInput({ value, onChange, onSubmit, loading }) {
  return (
    <form
      className="chat-input-wrapper"
      onSubmit={(event) => {
        event.preventDefault();
        if (value.trim() && !loading) {
          onSubmit();
        }
      }}
    >
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Ask TBX Insight about banks, balances, or transactions…"
        disabled={loading}
        aria-label="Message TBX Insight"
      />

      <button type="submit" disabled={!value.trim() || loading} aria-label="Send">
        {loading ? "…" : "↑"}
      </button>
    </form>
  );
}

export default ChatInput;
