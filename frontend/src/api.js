const configuredBase = (process.env.REACT_APP_API_BASE_URL || '').replace(/\/$/, '');
const isLocalDev = ['3000', '3001'].includes(window.location.port)
  || ['localhost', '127.0.0.1'].includes(window.location.hostname);

export const API_BASE_URL = configuredBase
  || (isLocalDev ? 'http://localhost:5000' : '/api');

export const apiUrl = (path) => `${API_BASE_URL}${path}`;

export async function postJSON(path, payload) {
  const response = await fetch(apiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return parseJSONResponse(response);
}

export async function getJSON(path) {
  const response = await fetch(apiUrl(path));
  return parseJSONResponse(response);
}

async function parseJSONResponse(response) {
  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (error) {
      throw new Error(`Invalid JSON from API (${response.status}): ${text.slice(0, 120)}`);
    }
  }

  if (!response.ok) {
    throw new Error(data.error || `API request failed with ${response.status}`);
  }
  return data;
}
