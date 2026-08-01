const REQUEST_TIMEOUT_MS = 45_000;

export function resolveApiBaseUrl(configuredBase = '', location = window.location) {
  const explicit = String(configuredBase || '').trim().replace(/\/$/, '');
  if (explicit) return explicit;
  const hostname = String(location?.hostname || '').toLowerCase();
  const port = String(location?.port || '');
  const local = hostname === 'localhost' || hostname === '127.0.0.1' || ['3000', '3001'].includes(port);
  return local ? 'http://localhost:5000' : '/api';
}

export const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
export const apiUrl = (path) => `${API_BASE_URL}${path}`;

export function postJSON(path, payload) {
  return requestJSON(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export function getJSON(path) {
  return requestJSON(path);
}

async function requestJSON(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(apiUrl(path), { ...options, signal: controller.signal });
    return await parseJSONResponse(response);
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error(`API request timed out after ${REQUEST_TIMEOUT_MS / 1000} seconds.`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function parseJSONResponse(response) {
  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      throw new Error(`Invalid JSON from API (${response.status}): ${text.slice(0, 120)}`);
    }
  }
  if (!response.ok) {
    const requestId = response.headers?.get?.('X-Request-ID');
    const suffix = requestId ? ` (request ${requestId})` : '';
    throw new Error(`${data.error || `API request failed with ${response.status}`}${suffix}`);
  }
  return data;
}
