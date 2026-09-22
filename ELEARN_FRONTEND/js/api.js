// Thin fetch wrapper for /api/v1/. Adds the Bearer header, turns DRF error bodies into
// ApiError, and drops the session on a 401 so the router can send the user to login.
import { getToken, clearSession } from './auth.js';

const CFG = window.ELEARN_CONFIG || {};
export const API_BASE = (CFG.API_BASE || location.origin).replace(/\/$/, '');
export const API_ROOT = API_BASE + '/api/v1/';
export const WS_BASE = API_BASE.replace(/^http/, 'ws');

export class ApiError extends Error {
  constructor(status, data) {
    super(messageOf(data, status));
    this.status = status;
    this.data = data;
  }
}

// DRF answers with {detail}, {non_field_errors: [...]} or {field: [...]}; flatten any of them
export function messageOf(data, status) {
  if (status === 0) return `Cannot reach the server at ${API_BASE}.`;
  if (!data) return `Request failed (${status}).`;
  if (typeof data === 'string') return data;
  if (data.detail) return String(data.detail);
  if (data.non_field_errors) return [].concat(data.non_field_errors).join(' ');
  const parts = Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(' ')}`);
  return parts.join(' · ') || `Request failed (${status}).`;
}

async function parseBody(res) {
  if (res.status === 204) return null;
  const text = await res.text();
  if (!text) return null;
  try { return JSON.parse(text); } catch { return text; }
}

export async function request(method, path, { body, query } = {}) {
  const url = new URL(/^https?:/.test(path) ? path : API_ROOT + path.replace(/^\//, ''));
  for (const [k, v] of Object.entries(query || {})) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v);
  }
  const headers = { Accept: 'application/json' };
  const token = getToken();
  if (token) headers.Authorization = 'Bearer ' + token;

  let payload;
  if (body instanceof FormData) {
    payload = stripEmptyFiles(body);           // browser sets the multipart boundary itself
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }

  let res;
  try {
    // credentials: 'omit' -> the browser never attaches a cookie, even on the same origin
    res = await fetch(url, { method, headers, body: payload, credentials: 'omit' });
  } catch {
    throw new ApiError(0, null);
  }
  const data = await parseBody(res);
  if (!res.ok) {
    if (res.status === 401 && token) {
      clearSession();
      window.dispatchEvent(new CustomEvent('elearn:unauthorized'));
    }
    throw new ApiError(res.status, data);
  }
  return data;
}

// an untouched <input type=file> still lands in FormData as an empty File, which DRF rejects
function stripEmptyFiles(fd) {
  for (const [k, v] of Array.from(fd.entries())) {
    if (v instanceof File && v.size === 0 && !v.name) fd.delete(k);
  }
  return fd;
}

export const api = {
  get: (path, query) => request('GET', path, { query }),
  post: (path, body) => request('POST', path, { body }),
  put: (path, body) => request('PUT', path, { body }),
  patch: (path, body) => request('PATCH', path, { body }),
  del: (path) => request('DELETE', path),
};

// list endpoints are paginated ({count, next, previous, results}); a few return bare arrays
export const rows = (data) => (Array.isArray(data) ? data : (data && data.results) || []);
