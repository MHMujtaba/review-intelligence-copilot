import { useState } from "react";

import { askQuestion, embedAsin, fetchInsights, fetchSummary, loadCsv } from "./api";
import ChatPanel from "./components/ChatPanel";
import InsightsPanel from "./components/InsightsPanel";

const DEFAULT_ASIN = "B000TEST123";
const DEFAULT_CSV_PATH = "C:/data/reviews.csv";

export default function App() {
  const [asin, setAsin] = useState(DEFAULT_ASIN);
  const [draftAsin, setDraftAsin] = useState(DEFAULT_ASIN);
  const [csvPath, setCsvPath] = useState(DEFAULT_CSV_PATH);
  const [summary, setSummary] = useState(null);
  const [insights, setInsights] = useState(null);
  const [previousResponseId, setPreviousResponseId] = useState(null);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Load a local CSV, build embeddings, then ask grounded questions about complaints, positives, or overall sentiment for a specific ASIN."
    }
  ]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLoadCsv() {
    setLoading(true);
    setError("");
    setPreviousResponseId(null);
    try {
      const response = await loadCsv(csvPath, 5000);
      setStatus(`Loaded ${response.loaded_reviews} reviews across ${response.unique_asins} ASINs.`);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleEmbed() {
    const targetAsin = draftAsin.trim() || asin;
    setAsin(targetAsin);
    setLoading(true);
    setError("");
    setPreviousResponseId(null);
    try {
      const response = await embedAsin(targetAsin);
      setStatus(`Indexed ${response.embedded_reviews} reviews for local semantic search on ${targetAsin}.`);
    } catch (embedError) {
      setError(embedError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadInsights() {
    const nextAsin = draftAsin.trim();
    if (!nextAsin) {
      return;
    }
    setAsin(nextAsin);
    setLoading(true);
    setError("");
    setPreviousResponseId(null);
    try {
      const [summaryResult, insightsResult] = await Promise.all([
        fetchSummary(nextAsin),
        fetchInsights(nextAsin)
      ]);
      setSummary(summaryResult);
      setInsights(insightsResult);
      setStatus(`Loaded review intelligence for ${nextAsin}.`);
    } catch (loadError) {
      setError(loadError.message);
      setSummary(null);
      setInsights(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleAsk(question) {
    const nextMessages = [...messages, { role: "user", content: question }];
    setMessages(nextMessages);
    setLoading(true);
    setError("");

    try {
      const response = await askQuestion(question, asin, previousResponseId);
      setPreviousResponseId(response.previous_response_id || null);
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: response.answer,
          meta: {
            queryType: response.query_type,
            evidence: response.evidence.length
          }
        }
      ]);
    } catch (askError) {
      setError(askError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">Local Review RAG</span>
          <h1>Review-Centric Intelligence</h1>
          <p>
            Load a CSV, build review-level FAISS embeddings, then ask grounded questions over
            review text with helpfulness-aware reranking.
          </p>
        </div>
        <div className="control-panel">
          <label>
            CSV File Path
            <input value={csvPath} onChange={(event) => setCsvPath(event.target.value)} />
          </label>
          <label>
            ASIN
            <input value={draftAsin} onChange={(event) => setDraftAsin(event.target.value)} />
          </label>
          <div className="control-actions">
            <button onClick={handleLoadCsv}>Load CSV</button>
            <button className="secondary" onClick={handleEmbed}>
              Build Embeddings
            </button>
            <button className="secondary" onClick={handleLoadInsights}>
              Load ASIN Insights
            </button>
          </div>
        </div>
      </div>

      {error ? <div className="status error">{error}</div> : null}
      {status ? <div className="status">{status}</div> : null}
      {loading ? <div className="status">Running local review intelligence pipeline...</div> : null}

      <div className="workspace-grid simple-grid">
        <ChatPanel messages={messages} onAsk={handleAsk} loading={loading} />
        <InsightsPanel asin={asin} summary={summary} insights={insights} />
      </div>
    </div>
  );
}
