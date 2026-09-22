// Hash router: #/courses/12?page=2 -> route '/courses/:id' with params {id: '12'} and
// query {page: '2'}. Hash URLs need no server rewrite, so any static file server works.

const routes = [];

export function route(pattern, handler, opts = {}) {
  const keys = [];
  const source = pattern.replace(/\/:(\w+)/g, (_, key) => {
    keys.push(key);
    return '/([^/]+)';
  });
  routes.push({ regex: new RegExp('^' + source + '/?$'), keys, handler, ...opts });
}

export function parseLocation() {
  const hash = location.hash.replace(/^#/, '') || '/';
  const [rawPath, qs = ''] = hash.split('?');
  const path = rawPath.startsWith('/') ? rawPath : '/' + rawPath;
  return { path, search: qs, query: Object.fromEntries(new URLSearchParams(qs)) };
}

export function match(path) {
  for (const r of routes) {
    const m = r.regex.exec(path);
    if (!m) continue;
    const params = {};
    r.keys.forEach((k, i) => { params[k] = decodeURIComponent(m[i + 1]); });
    return { route: r, params };
  }
  return null;
}

export function navigate(path, { replace = false } = {}) {
  if (replace) location.replace('#' + path);
  else location.hash = path;
}

export function start(dispatch) {
  window.addEventListener('hashchange', dispatch);
  dispatch();
}

// builds "#/path?x=1" from parts, url-encoding the values
export function link(path, query) {
  const qs = query ? new URLSearchParams(
    Object.entries(query).filter(([, v]) => v !== undefined && v !== null && v !== '')).toString() : '';
  return '#' + path + (qs ? '?' + qs : '');
}

export const seg = encodeURIComponent;

// A `next=` handed back by the login screen is a path inside this app and nothing else:
// anything absolute or protocol-relative is discarded rather than navigated to.
export function safePath(value, fallback = '/me') {
  return typeof value === 'string' && /^\/(?!\/)/.test(value) ? value : fallback;
}
