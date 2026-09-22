// The logged-in user: me/, me/status/, me/courses/ and profile editing.
import { api, rows } from '../api.js';
import { updateUser, clearSession } from '../auth.js';
import { navigate, link } from '../router.js';
import {
  html, mount, field, onSubmit, onAction, toast, spinner, errorBox, courseGrid, pager,
  avatar, fullName, fmtTime, setTitle, PASSWORD_RULE,
} from '../ui.js';

export async function dashboard({ el, query, user }) {
  setTitle('Dashboard');
  const isTutor = user.user_cat === 'instructor';
  const page = Number(query.page) || 1;

  mount(el, html`<section class="dash">
    <div class="cols">
      <aside>
        <div class="card pad profile">
          ${avatar(user, 'lg')}
          <h2>${fullName(user)}</h2>
          <p class="muted">@${user.USER_NAME} · ${isTutor ? 'Tutor' : 'Learner'}</p>
          <p class="muted small">${user.EMAIL}<br>${user.PHONE || ''}</p>
          ${user.last_login ? html`<p class="muted small">Last login ${fmtTime(user.last_login)}</p>` : ''}
          <a class="btn ghost block" href="${link('/me/edit')}">Edit profile</a>
          ${isTutor ? html`<a class="btn ghost block" href="${link('/teach')}">Teaching tools</a>` : ''}
          <a class="btn ghost block" href="${link('/messages')}">Messages</a>
        </div>
        <div class="card pad" id="status">
          <h3>Status</h3>
          <p class="muted small">Shown on your public page for 30 days.</p>
          ${spinner()}
        </div>
      </aside>
      <div class="main">
        <h1>${isTutor ? 'My courses' : 'Enrolled courses'}</h1>
        <div id="courses">${spinner()}</div>
      </div>
    </div>
  </section>`);

  // ---- status
  const statusBox = el.querySelector('#status');
  try {
    const { status } = await api.get('me/status/');
    mount(statusBox, html`<h3>Status</h3>
      <p class="muted small">Shown on your public page for 30 days.</p>
      <form id="status-form" class="form">
        <div class="field"><textarea name="status" rows="3" maxlength="500" placeholder="What are you up to?">${status || ''}</textarea>
          <small class="field-error" data-error-for="status"></small></div>
        <p class="form-error"></p>
        <div class="row">
          <button class="btn primary" type="submit">Save</button>
          ${status ? html`<button class="btn ghost" type="button" data-action="clear">Clear</button>` : ''}
        </div>
      </form>`);
    onSubmit(statusBox.querySelector('#status-form'), async (fd) => {
      await api.put('me/status/', { status: fd.get('status') });
      toast('Status saved.', 'success');
    });
    onAction(statusBox, {
      clear: async () => {
        await api.del('me/status/');
        statusBox.querySelector('textarea').value = '';
        toast('Status cleared.');
      },
    });
  } catch (err) {
    mount(statusBox, errorBox(err));
  }

  // ---- courses
  const coursesBox = el.querySelector('#courses');
  try {
    const data = await api.get('me/courses/', { page });
    const list = rows(data);
    mount(coursesBox, html`
      ${list.length ? courseGrid(list)
        : isTutor ? html`<p class="empty">You have not created a course yet. <a href="${link('/teach/courses/new')}">Create one</a>.</p>`
                  : html`<p class="empty">You are not enrolled anywhere yet. <a href="${link('/')}">Browse the catalogue</a>.</p>`}
      ${pager(data, page)}`);
    onAction(coursesBox, { page: ({ page: p }) => navigate(link('/me', { page: p }).slice(1)) });
  } catch (err) {
    mount(coursesBox, errorBox(err));
  }
}

export function editProfile({ el, user }) {
  setTitle('Edit profile');
  mount(el, html`<section class="narrow">
    <h1>Edit profile</h1>
    <form id="profile" class="card form" enctype="multipart/form-data">
      <div class="row center">${avatar(user, 'lg')} <span class="muted">@${user.USER_NAME} · ${user.EMAIL}</span></div>
      <div class="two">
        ${field({ label: 'First name', name: 'FIRST_NAME', value: user.FIRST_NAME || '', required: true })}
        ${field({ label: 'Last name', name: 'LAST_NAME', value: user.LAST_NAME || '', required: true })}
      </div>
      ${field({ label: 'Phone', name: 'PHONE', type: 'tel', value: user.PHONE || '', required: true, max: 15 })}
      ${field({ label: 'New picture', name: 'PICTURE', type: 'file', accept: 'image/*', hint: 'Leave empty to keep the current one' })}
      ${field({ label: 'New password', name: 'PASSWORD', type: 'password', ...PASSWORD_RULE,
        hint: `Leave empty to keep it (${PASSWORD_RULE.hint}). Changing it logs you out everywhere.` })}
      <p class="form-error"></p>
      <button class="btn primary" type="submit">Save changes</button>
    </form>

    <div class="card pad danger-zone">
      <h3>Delete account</h3>
      <p class="muted small">Removes your profile${user.user_cat === 'instructor' ? ', your courses and their enrolments' : ' and your enrolments'}. This cannot be undone.</p>
      <button class="btn danger" data-action="delete">Delete my account</button>
    </div>
  </section>`);

  onSubmit(el.querySelector('#profile'), async (fd) => {
    const changingPassword = Boolean(fd.get('PASSWORD'));
    if (!changingPassword) fd.delete('PASSWORD');
    const data = await api.patch('me/', fd);
    if (changingPassword) {
      // the token carries a password fingerprint, so it just became invalid
      clearSession();
      window.dispatchEvent(new CustomEvent('elearn:session'));
      toast('Password changed. Please log in again.', 'success', 6000);
      navigate(link('/login', { user_type: user.user_cat, email: user.EMAIL }).slice(1), { replace: true });
      return;
    }
    updateUser(data);
    window.dispatchEvent(new CustomEvent('elearn:session'));
    toast('Profile saved.', 'success');
    navigate('/me');
  });

  onAction(el, {
    delete: async () => {
      if (!confirm('Delete your account permanently?')) return;
      if (!confirm('Last chance: this cannot be undone. Continue?')) return;
      await api.del('me/');
      clearSession();
      window.dispatchEvent(new CustomEvent('elearn:session'));
      toast('Account deleted.');
      navigate('/', { replace: true });
    },
  });
}
