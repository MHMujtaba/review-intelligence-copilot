const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json();
}

export function loadCsv(filePath, chunksize) {
  return request("/load_csv", {
    method: "POST",
    body: JSON.stringify({
      file_path: filePath,
      chunksize: chunksize || null
    })
  });
}

export function fetchSummary(asin) {
  return request(`/summary/${asin}`);
}

export function fetchInsights(asin) {
  return request(`/insights/${asin}`);
}

export function askQuestion(query, asin, previousResponseId = null) {
  return request("/ask", {
    method: "POST",
    body: JSON.stringify({
      query,
      asin: asin || null,
      max_results: 8,
      previous_response_id: previousResponseId
    })
  });
}

export function searchReviews(query, asin, topK = 8) {
  return request("/search", {
    method: "POST",
    body: JSON.stringify({
      query,
      asin: asin || null,
      top_k: topK
    })
  });
}

export function embedAsin(asin) {
  return request("/embed", {
    method: "POST",
    body: JSON.stringify({
      asin: asin || null,
      batch_size: 64,
      rebuild_index: true
    })
  });
}
