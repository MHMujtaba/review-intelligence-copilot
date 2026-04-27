import { useState } from "react";

export default function ChatPanel({ messages, onAsk, loading }) {
  const [draft, setDraft] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || loading) {
      return;
    }
    setDraft("");
    await onAsk(trimmed);
  }

  return (
    <section className="chat-panel">
      <div className="card-header">
        <h3>Review Chat</h3>
        <span>FAISS retrieval + reranking</span>
      </div>

      <div className="chat-transcript">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
            <span className="message-role">{message.role === "assistant" ? "Copilot" : "You"}</span>
            <p>{message.content}</p>
            {message.meta ? (
              <small>
                {message.meta.queryType} | {message.meta.evidence} evidence reviews
              </small>
            ) : null}
          </div>
        ))}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask about complaints, positive themes, helpful reviews, or overall sentiment..."
          rows={4}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Running pipeline..." : "Ask Copilot"}
        </button>
      </form>
    </section>
  );
}
