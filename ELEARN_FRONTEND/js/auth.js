// Session = the JWT from auth/login/ plus the profile it came with. Kept in localStorage and
// sent as a header on every call; the SPA never uses cookies. localStorage can be missing or
// throw (private mode), so every access is guarded.

const TOKEN_KEY = 'elearn.token';
const USER_KEY = 'elearn.user';

function read(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

function write(key, value) {
  try {
    if (value == null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch { /* storage unavailable: the session just lives for this page load */ }
}

let memory = { token: read(TOKEN_KEY), user: safeParse(read(USER_KEY)) };

function safeParse(text) {
  try { return text ? JSON.parse(text) : null; } catch { return null; }
}

// the payload is plain base64url JSON: readable without any library, never trusted for auth
export function decodePayload(token) {
  try {
    const body = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(body));
  } catch { return null; }
}

export function isExpired(token) {
  const payload = token && decodePayload(token);
  return !payload || !payload.exp || payload.exp * 1000 <= Date.now();
}

export function getToken() {
  if (memory.token && isExpired(memory.token)) clearSession();
  return memory.token;
}

export function currentUser() {
  return getToken() ? memory.user : null;
}

export function setSession(token, user) {
  memory = { token, user };
  write(TOKEN_KEY, token);
  write(USER_KEY, JSON.stringify(user));
}

export function updateUser(user) {
  memory.user = user;
  write(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  memory = { token: null, user: null };
  write(TOKEN_KEY, null);
  write(USER_KEY, null);
}
