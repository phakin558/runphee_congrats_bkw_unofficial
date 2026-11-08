const GAS_URL = process.env.GAS_WEB_APP_URL;
const ALLOWED_ACTIONS = new Set(['getStudentData', 'getUniqueUniversities', 'health']);

function response(body, status = 200, maxAge = 60) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': `public, s-maxage=${maxAge}, stale-while-revalidate=300`,
      'access-control-allow-origin': '*',
    },
  });
}

export async function GET(request) {
  if (!GAS_URL) return response({ ok: false, error: 'Missing GAS_WEB_APP_URL' }, 500, 0);

  const incoming = new URL(request.url);
  const action = incoming.searchParams.get('action') || 'getStudentData';
  if (!ALLOWED_ACTIONS.has(action)) return response({ ok: false, error: 'Unsupported action' }, 400, 0);

  const upstreamUrl = `${GAS_URL}${GAS_URL.includes('?') ? '&' : '?'}action=${encodeURIComponent(action)}`;
  try {
    const upstream = await fetch(upstreamUrl, { cache: 'no-store' });
    const payload = await upstream.json();
    if (!upstream.ok || payload.ok === false) {
      return response({ ok: false, error: payload.error || `GAS request failed (${upstream.status})` }, 502, 0);
    }
    const maxAge = action === 'health' ? 15 : action === 'getUniqueUniversities' ? 300 : 60;
    return response(payload, 200, maxAge);
  } catch (error) {
    return response({ ok: false, error: error.message || 'Unable to reach GAS' }, 502, 0);
  }
}

export async function OPTIONS() {
  return new Response(null, {
    status: 204,
    headers: {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET, OPTIONS',
    },
  });
}
