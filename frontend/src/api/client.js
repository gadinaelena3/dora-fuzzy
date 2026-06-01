// Thin wrapper around the FastAPI backend.
// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js)
// In Docker compose, the same /api path is served by nginx -> backend.

const API = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch { /* keep statusText */ }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  assess: (payload) =>
    request('/assess', { method: 'POST', body: JSON.stringify(payload) }),

  assessBatch: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return fetch(`${API}/assess-batch`, { method: 'POST', body: fd })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || res.statusText);
        }
        return res.json();
      });
  },

  membershipCurves: () => request('/membership-curves'),
  rules: () => request('/rules'),
  ruleModes: () => request('/rule-modes'),
  study: (ruleMode = 'base12') => request(`/study?rule_mode=${ruleMode}`),
  sensitivity: () => request('/study/sensitivity'),
};
