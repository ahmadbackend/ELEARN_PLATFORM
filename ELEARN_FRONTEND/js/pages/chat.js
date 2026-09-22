// Learner <-> tutor private chat.
//   inbox : GET peer-chats/
//   room  : GET peer-chats/{tutor}/{learner}/ for the last 20 messages, then the websocket
//           ws/peerchat/{tutor}/{learner}/?token=<jwt> for everything live. Messages are sent
//           over the socket; if it cannot be opened the page falls back to POST + polling
//           with ?after=<id> so the conversation still works.
import { api, WS_BASE, ApiError } from '../api.js';
import { getToken } from '../auth.js';
import { link, seg } from '../router.js';
import {
  html, mount, spinner, empty, errorBox, toast, avatar, fullName, profileLink, fmtTime, setTitle,
} from '../ui.js';

const HISTORY = 20;
const HISTORY_MAX = 200;
const POLL_MS = 5000;

export async function inbox({ el }) {
  setTitle('Messages');
  mount(el, html`<section class="narrow"><h1>Messages</h1><div id="list">${spinner()}</div></section>`);
  const list = el.querySelector('#list');
  try {
    const convs = await api.get('peer-chats/');
    mount(list, convs.length ? html`<ul class="inbox card">${convs.map((cv) => html`
      <li>
        <a href="${link(`/messages/${seg(cv.instructorName)}/${seg(cv.studentName)}`)}">
          ${avatar(cv.partner, 'md')}
          <span class="who">
            <strong>${fullName(cv.partner)}</strong>
            <span class="muted small">${cv.partner.user_cat === 'instructor' ? 'Tutor' : 'Learner'} · @${cv.partner.USER_NAME}</span>
            <span class="preview ${cv.last ? '' : 'muted'}">${cv.last ? cv.last.message : 'No messages yet'}</span>
          </span>
          <span class="muted small when">${cv.last ? fmtTime(cv.last.TimeStamp) : ''}</span>
        </a>
      </li>`)}</ul>`
      : html`<p class="empty">No conversations yet. Learners can message the tutor of any course they are enrolled in;
          tutors find their learners under <a href="${link('/teach/learners')}">Learners</a>.</p>`);
  } catch (err) {
    mount(list, errorBox(err));
  }
}

export async function room({ el, params, user }) {
  const tutor = params.tutor;
  const learner = params.learner;
  const path = `peer-chats/${seg(tutor)}/${seg(learner)}/`;
  const partnerName = user.user_cat === 'student' ? tutor : learner;
  const partnerCat = user.user_cat === 'student' ? 'instructor' : 'student';
  setTitle(`Chat with ${partnerName}`);

  mount(el, html`<section class="chat-page">
    <header class="chat-head">
      <a class="muted small" href="${link('/messages')}">‹ Messages</a>
      <h1><a href="${profileLink({ USER_NAME: partnerName, user_cat: partnerCat })}">${partnerName}</a>
        <span class="muted small">${partnerCat === 'instructor' ? 'tutor' : 'learner'}</span></h1>
      <span id="conn" class="conn connecting">connecting…</span>
    </header>
    <div id="log" class="chat-log">${spinner()}</div>
    <form id="send" class="chat-send">
      <input name="message" maxlength="1000" autocomplete="off" placeholder="Write a message…" required>
      <button class="btn primary" type="submit">Send</button>
    </form>
  </section>`);

  const log = el.querySelector('#log');
  const conn = el.querySelector('#conn');
  const form = el.querySelector('#send');
  const input = form.message;

  let limit = HISTORY;
  let lastId = 0;          // highest REST id seen, for ?after= polling
  let ws = null;
  let live = false;
  let pollTimer = null;
  let closed = false;      // set by the route cleanup so late socket events are ignored

  function setConn(state, text) {
    conn.className = `conn ${state}`;
    conn.textContent = text;
  }

  function bubble(m) {
    // REST rows carry sender_cat + ISO TimeStamp; socket frames carry userCat + a preformatted time
    const cat = m.sender_cat || m.userCat;
    const mine = cat === user.user_cat;
    const when = m.TimeStamp || m.timeStamp;
    return html`<div class="msg ${mine ? 'mine' : 'theirs'}">
      <div class="text">${m.message}</div>
      <div class="muted tiny">${mine ? 'you' : (m.sender ? fullName(m.sender) : m.userName)} · ${fmtTime(when)}</div>
    </div>`;
  }

  function append(m) {
    const placeholder = log.querySelector('.empty');
    if (placeholder) placeholder.remove();
    const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 40;
    log.insertAdjacentHTML('beforeend', String(bubble(m)));
    if (atBottom || (m.userCat || m.sender_cat) === user.user_cat) log.scrollTop = log.scrollHeight;
  }

  async function loadHistory() {
    const msgs = await api.get(path, { limit });
    lastId = msgs.reduce((max, m) => Math.max(max, m.id), 0);
    mount(log, html`
      ${msgs.length >= limit && limit < HISTORY_MAX ? html`<button class="linklike small" id="more">Load earlier messages</button>` : ''}
      ${msgs.length ? msgs.map(bubble) : empty('No messages yet. Say hello!')}`);
    log.scrollTop = log.scrollHeight;
    const more = log.querySelector('#more');
    if (more) more.addEventListener('click', async () => {
      limit = Math.min(limit * 2, HISTORY_MAX);
      more.disabled = true;
      try { await loadHistory(); } catch (err) { toast(err.message, 'error'); }
    });
  }

  // ---- websocket (primary)
  function connect() {
    const token = getToken();
    if (!token || closed) return;
    try {
      ws = new WebSocket(`${WS_BASE}/ws/peerchat/${seg(tutor)}/${seg(learner)}/?token=${encodeURIComponent(token)}`);
    } catch {
      startPolling();
      return;
    }
    ws.onopen = () => {
      if (closed) { ws.close(); return; }
      live = true;
      stopPolling();
      setConn('live', 'live');
    };
    ws.onmessage = (e) => {
      try { append(JSON.parse(e.data)); } catch { /* ignore malformed frames */ }
    };
    ws.onerror = () => { /* onclose follows and handles the fallback */ };
    ws.onclose = () => {
      const wasLive = live;
      live = false;
      ws = null;
      if (closed) return;
      // the server closes the socket when the pair may no longer chat (dropped course or a
      // block); it also closes on a lost connection, in which case polling keeps things going.
      // socket frames carry no id, so re-read the history before polling with ?after=
      const resync = wasLive ? loadHistory().catch(() => {}) : Promise.resolve();
      resync.then(startPolling);
      setConn('offline', wasLive ? 'reconnecting…' : 'offline · using polling');
      setTimeout(() => { if (!closed && !live) connect(); }, 10000);
    };
  }

  // ---- REST polling (fallback)
  async function poll() {
    try {
      const fresh = await api.get(path, { after: lastId, limit: HISTORY_MAX });
      for (const m of fresh) {
        lastId = Math.max(lastId, m.id);
        append(m);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        stopPolling();
        setConn('offline', 'conversation closed');
        toast(err.message, 'error', 6000);
      }
    }
  }
  function startPolling() {
    if (pollTimer || closed) return;
    pollTimer = setInterval(poll, POLL_MS);
  }
  function stopPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = null;
  }

  // ---- sending
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = '';
    if (live && ws && ws.readyState === WebSocket.OPEN) {
      // the server saves it and echoes it to every party in the room, including us
      ws.send(JSON.stringify({ message }));
      return;
    }
    try {
      const saved = await api.post(path, { message });
      lastId = Math.max(lastId, saved.id);
      append(saved);
    } catch (err) {
      input.value = message;
      toast(err.message, 'error');
    }
  });

  try {
    await loadHistory();
  } catch (err) {
    mount(log, errorBox(err));
    setConn('offline', 'unavailable');
    form.querySelector('button').disabled = true;
    return;
  }
  connect();
  input.focus();

  // route cleanup: stop the socket and the poller when the user navigates away
  return () => {
    closed = true;
    stopPolling();
    if (ws) { try { ws.close(); } catch { /* already closed */ } }
  };
}
