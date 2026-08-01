import { getJSON, postJSON, resolveApiBaseUrl } from './api';

function response({ ok = true, status = 200, body = '', requestId = null } = {}) {
  return {
    ok,
    status,
    text: async () => body,
    headers: { get: () => requestId },
  };
}

describe('BioAgents API client', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('posts JSON to the local backend during React development', async () => {
    fetch.mockResolvedValue(response({ body: '{"status":"ok"}' }));

    await expect(postJSON('/query', { type: 'compound' })).resolves.toEqual({ status: 'ok' });

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:5000/query',
      expect.objectContaining({
        method: 'POST',
        body: '{"type":"compound"}',
        signal: expect.anything(),
      }),
    );
  });

  test('uses same-origin API routes in production and honors explicit configuration', () => {
    expect(resolveApiBaseUrl('', { hostname: 'bioagents.vercel.app' })).toBe('/api');
    expect(resolveApiBaseUrl('https://api.example.com/', { hostname: 'bioagents.vercel.app' }))
      .toBe('https://api.example.com');
  });

  test('includes the server request id in API errors', async () => {
    fetch.mockResolvedValue(response({
      ok: false,
      status: 400,
      body: '{"error":"Invalid molecule"}',
      requestId: 'request-123',
    }));

    await expect(getJSON('/molecules')).rejects.toThrow('Invalid molecule (request request-123)');
  });

  test('rejects non-JSON success responses instead of hiding deployment routing errors', async () => {
    fetch.mockResolvedValue(response({ body: '<!doctype html>' }));

    await expect(getJSON('/health')).rejects.toThrow('Invalid JSON from API (200)');
  });
});
