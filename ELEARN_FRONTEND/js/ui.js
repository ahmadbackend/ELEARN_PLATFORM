// Rendering helpers. `html` is a tagged template that escapes every interpolated value, so
// server data (names, reviews, chat messages) can never inject markup; nested html`` results
// and `raw()` pass through untouched.
import { ApiError } from './api.js';
import { link, seg } from './router.js';

class Raw {
  constructor(s) { this.s = s; }
  toString() { return this.s; }
}

export const raw = (s) => new Raw(String(s));

export function esc(value) {
  return String(value).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function render(v) {
  if (v == null || v === false) return '';
  if (v instanceof Raw) return v.s;
  if (Array.isArray(v)) return v.map(render).join('');
  return esc(v);
}

export function html(strings, ...values) {
  let out = '';
  strings.forEach((s, i) => { out += s + (i < values.length ? render(values[i]) : ''); });
  return new Raw(out);
}

export function mount(el, tpl) {
  el.innerHTML = String(tpl);
  return el;
}

// replaces a node with an empty clone of itself: drops its children and every listener
export function fresh(node) {
  const clone = node.cloneNode(false);
  node.replaceWith(clone);
  return clone;
}

export function setTitle(text) {
  document.title = text ? `${text} · ELEARN` : 'ELEARN';
}

// ----------------------------------------------------------------------------- feedback
export function toast(message, kind = 'info', ms = 4000) {
  const box = document.getElementById('toasts');
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.textContent = message;
  box.appendChild(el);
  setTimeout(() => el.classList.add('show'), 10);
  setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, ms);
}

export const spinner = () => html`<div class="spinner" role="status" aria-label="loading"></div>`;

export const empty = (text) => html`<p class="empty">${text}</p>`;

export function errorBox(err) {
  const msg = err instanceof ApiError ? err.message : (err && err.message) || 'Something went wrong.';
  return html`<div class="notice error"><strong>Error.</strong> ${msg}</div>`;
}

// ----------------------------------------------------------------------------- forms
// mirrors the RegexValidator on STUDENT/INSTRUCTOR.PASSWORD so the browser rejects the same input
export const PASSWORD_RULE = {
  min: 8, max: 12, pattern: String.raw`(?=.*[a-z])(?=.*\d)[a-zA-Z\d]{8,12}`,
  hint: '8 to 12 letters and digits, with at least one lowercase letter and one digit',
};

export function field({ label, name, type = 'text', value = '', required = false, hint = '',
  placeholder = '', min, max, accept, rows, pattern }) {
  const attrs = html`name="${name}" id="f-${name}" ${required ? 'required' : ''}
    ${placeholder ? html`placeholder="${placeholder}"` : ''}
    ${min != null ? html`minlength="${min}"` : ''} ${max != null ? html`maxlength="${max}"` : ''}
    ${pattern ? html`pattern="${pattern}" title="${hint}"` : ''}
    ${accept ? html`accept="${accept}"` : ''}`;
  const input = type === 'textarea'
    ? html`<textarea ${attrs} rows="${rows || 4}">${value}</textarea>`
    : html`<input type="${type}" ${attrs} value="${type === 'file' ? '' : value}">`;
  return html`<div class="field">
    <label for="f-${name}">${label}${required ? html` <span class="req">*</span>` : ''}</label>
    ${input}
    ${hint ? html`<small class="hint">${hint}</small>` : ''}
    <small class="field-error" data-error-for="${name}"></small>
  </div>`;
}

export function roleSelect(name = 'user_type', value = 'student') {
  return html`<div class="field">
    <label>I am a</label>
    <div class="segmented">
      <label><input type="radio" name="${name}" value="student" ${value === 'student' ? 'checked' : ''}> Learner</label>
      <label><input type="radio" name="${name}" value="instructor" ${value === 'instructor' ? 'checked' : ''}> Tutor</label>
    </div>
    <small class="field-error" data-error-for="${name}"></small>
  </div>`;
}

export function showFormErrors(form, err) {
  form.querySelectorAll('.field-error, .form-error').forEach((e) => { e.textContent = ''; });
  const top = form.querySelector('.form-error');
  const leftovers = [];
  const data = err && err.data;
  if (data && typeof data === 'object') {
    for (const [key, val] of Object.entries(data)) {
      const msg = [].concat(val).join(' ');
      const slot = form.querySelector(`[data-error-for="${key}"]`);
      if (slot) slot.textContent = msg;
      else leftovers.push(key === 'detail' || key === 'non_field_errors' ? msg : `${key}: ${msg}`);
    }
  } else {
    leftovers.push(err.message);
  }
  if (top) top.textContent = leftovers.join(' ');
  else if (leftovers.length) toast(leftovers.join(' '), 'error');
}

// submit handler with the button disabled while the request runs and DRF errors mapped
// back onto the fields
export function onSubmit(form, handler) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = form.querySelector('[type=submit]');
    form.querySelectorAll('.field-error, .form-error').forEach((x) => { x.textContent = ''; });
    if (button) button.disabled = true;
    try {
      await handler(new FormData(form), form);
    } catch (err) {
      if (err instanceof ApiError && err.status !== 0) showFormErrors(form, err);
      else toast(err.message || String(err), 'error');
    } finally {
      if (button) button.disabled = false;
    }
  });
}

export const jsonFrom = (fd) => Object.fromEntries(fd.entries());

// buttons carrying data-action="x": one delegated listener per page
export function onAction(root, handlers) {
  root.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn || !root.contains(btn)) return;
    const fn = handlers[btn.dataset.action];
    if (!fn) return;
    e.preventDefault();
    btn.disabled = true;
    try { await fn(btn.dataset, btn); } catch (err) { toast(err.message || String(err), 'error'); }
    finally { btn.disabled = false; }
  });
}

// ----------------------------------------------------------------------------- formatting
export function fmtDate(v) {
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? String(v ?? '') :
    d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export function fmtTime(v) {
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? String(v ?? '') :
    d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

// "1 lecture" / "3 lectures"; pass the plural when it is not just a trailing s
export function plural(n, one, many = one + 's') {
  return `${n} ${Number(n) === 1 ? one : many}`;
}

export function fullName(u) {
  return u ? [u.FIRST_NAME, u.LAST_NAME].filter(Boolean).join(' ') || u.USER_NAME : '';
}

export function profileLink(u) {
  return u.user_cat === 'instructor' ? link(`/instructors/${seg(u.USER_NAME)}`) : link(`/students/${seg(u.USER_NAME)}`);
}

export function avatar(u, size = 'md') {
  // `''[0]` is undefined, so each initial is taken only when the name is there
  const first = (u.FIRST_NAME || u.USER_NAME || '').charAt(0);
  const last = (u.LAST_NAME || '').charAt(0);
  const initials = (first + last).toUpperCase() || '?';
  return u.PICTURE
    ? html`<img class="avatar ${size}" src="${u.PICTURE}" alt="">`
    : html`<span class="avatar ${size} initials">${initials}</span>`;
}

export function stars(avg) {
  const n = Math.round(Number(avg) || 0);
  return html`<span class="stars" aria-label="${n} of 5">${'★'.repeat(n)}${'☆'.repeat(5 - n)}</span>`;
}

export function ratingLine(rating) {
  if (!rating || !rating.count) return html`<span class="muted">No ratings yet</span>`;
  return html`${stars(rating.average)} <strong>${rating.average}</strong> <span class="muted">(${rating.count})</span>`;
}

export function courseCard(c, { href } = {}) {
  return html`<a class="card course" href="${href || link(`/courses/${c.id}`)}">
    <div class="cover">
      ${c.COVER_PHOTO ? html`<img src="${c.COVER_PHOTO}" alt="" loading="lazy">` : ''}
      ${c.IsDraft ? html`<span class="badge draft">Draft</span>` : ''}
    </div>
    <div class="card-body">
      <h3>${c.COURSE_NAME}</h3>
      <p class="muted">by ${fullName(c.instructor)}</p>
      <p class="meta">${ratingLine(c.rating)}</p>
      <p class="meta muted">${plural(c.lecture_count, 'lecture')} · ${c.enrolled_count} enrolled</p>
    </div>
  </a>`;
}

export function courseGrid(courses, opts) {
  if (!courses.length) return empty('No courses here yet.');
  return html`<div class="grid">${courses.map((c) => courseCard(c, opts))}</div>`;
}

// previous / next controls for a DRF page; the caller re-renders with the new page number
export function pager(data, page) {
  if (!data || (!data.next && !data.previous)) return '';
  return html`<div class="pager">
    <button class="btn ghost" data-action="page" data-page="${page - 1}" ${data.previous ? '' : 'disabled'}>‹ Previous</button>
    <span class="muted">Page ${page}${data.count != null ? html` · ${data.count} total` : ''}</span>
    <button class="btn ghost" data-action="page" data-page="${page + 1}" ${data.next ? '' : 'disabled'}>Next ›</button>
  </div>`;
}

export function fileName(url) {
  try { return decodeURIComponent(new URL(url).pathname.split('/').pop()); } catch { return 'file'; }
}
