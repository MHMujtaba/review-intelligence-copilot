function ThemeList({ title, items, empty }) {
  return (
    <div className="insight-card">
      <div className="card-header">
        <h3>{title}</h3>
      </div>
      <ul className="theme-list">
        {(items?.length ? items : [empty]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function ScaleReference({ title, markers, note }) {
  return (
    <div className="scale-reference">
      <span className="scale-title">{title}</span>
      <div className="scale-bar" aria-hidden="true">
        <div className="scale-fill" />
      </div>
      <div className="scale-markers">
        {markers.map((marker) => (
          <span key={marker}>{marker}</span>
        ))}
      </div>
      <small>{note}</small>
    </div>
  );
}

export default function InsightsPanel({ asin, summary, insights }) {
  const sentiment = insights?.sentiment_summary;
  const helpfulness = insights?.helpfulness_summary;

  return (
    <section className="insights-stack">
      <div className="insight-card">
        <div className="card-header">
          <h3>ASIN Scope</h3>
        </div>
        <p className="info-line">{asin || "No ASIN selected"}</p>
      </div>

      <div className="insight-card">
        <div className="card-header">
          <h3>Structured Summary</h3>
        </div>
        <p className="summary-copy">{summary?.summary || "Load an ASIN summary after indexing reviews."}</p>
      </div>

      <div className="insight-card">
        <div className="card-header">
          <h3>Sentiment Snapshot</h3>
        </div>
        <div className="insight-metrics">
          <span>Avg rating: {sentiment?.average_rating ?? "-"}</span>
          <span>Avg sentiment: {sentiment?.average_sentiment_score ?? "-"}</span>
          <span>Reviews: {sentiment?.review_count ?? "-"}</span>
        </div>
        <ScaleReference
          title="Reference scales"
          markers={["Sentiment -1.0", "0.0 neutral", "+1.0 positive"]}
          note="Average rating is on a separate 1.0 to 5.0 scale."
        />
      </div>

      <div className="insight-card">
        <div className="card-header">
          <h3>Helpfulness Snapshot</h3>
        </div>
        <div className="insight-metrics">
          <span>Avg helpfulness: {helpfulness?.average_helpfulness_ratio ?? "-"}</span>
          <span>High helpfulness: {helpfulness?.high_helpfulness_reviews ?? "-"}</span>
          <span>Low helpfulness: {helpfulness?.low_helpfulness_reviews ?? "-"}</span>
        </div>
        <ScaleReference
          title="Helpfulness ratio scale"
          markers={["0.0 low", "0.5 mixed", "1.0 high"]}
          note="Helpfulness ratio is computed as helpful_votes / (total_votes + 1)."
        />
      </div>

      <ThemeList
        title="Top Positive Themes"
        items={insights?.top_positive_themes}
        empty="No clear positive themes found."
      />
      <ThemeList
        title="Top Negative Themes"
        items={insights?.top_negative_themes}
        empty="No clear negative themes found."
      />
    </section>
  );
}
