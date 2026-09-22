// Public pages: instructors/{username}/ (anyone) and students/{username}/ (logged in only).
import { api } from '../api.js';
import { link, seg } from '../router.js';
import { html, mount, errorBox, courseGrid, avatar, fullName, setTitle } from '../ui.js';

async function profilePage(el, path, { heading, user, partnerLink }) {
  let p;
  try { p = await api.get(path); } catch (err) { mount(el, errorBox(err)); return; }
  setTitle(fullName(p));
  const chat = partnerLink && partnerLink(p);
  mount(el, html`<section class="profile-page">
    <div class="card pad profile wide">
      ${avatar(p, 'lg')}
      <div>
        <h1>${fullName(p)}</h1>
        <p class="muted">@${p.USER_NAME} · ${p.user_cat === 'instructor' ? 'Tutor' : 'Learner'}</p>
        ${p.status ? html`<blockquote class="status">${p.status}</blockquote>` : html`<p class="muted small">No status posted.</p>`}
        ${chat ? html`<a class="btn primary" href="${chat}">💬 Message</a>` : ''}
        ${user && user.USER_NAME === p.USER_NAME && user.user_cat === p.user_cat
          ? html`<a class="btn ghost" href="${link('/me/edit')}">Edit profile</a>` : ''}
      </div>
    </div>
    <h2>${heading}</h2>
    ${courseGrid(p.courses || [])}
  </section>`);
}

export function instructorProfile({ el, params, user }) {
  return profilePage(el, `instructors/${seg(params.username)}/`, {
    heading: 'Published courses',
    user,
    // a learner can message a tutor only when enrolled in one of their courses; the room
    // itself enforces that, so the link is offered and the API answers 403 otherwise
    partnerLink: (p) => (user && user.user_cat === 'student'
      ? link(`/messages/${seg(p.USER_NAME)}/${seg(user.USER_NAME)}`) : null),
  });
}

export function studentProfile({ el, params, user }) {
  return profilePage(el, `students/${seg(params.username)}/`, {
    heading: 'Enrolled courses',
    user,
    partnerLink: (p) => (user && user.user_cat === 'instructor'
      ? link(`/messages/${seg(user.USER_NAME)}/${seg(p.USER_NAME)}`) : null),
  });
}
