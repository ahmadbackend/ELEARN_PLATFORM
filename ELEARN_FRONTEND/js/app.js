// Entry point: route table, auth guards, the top navigation and global session events.
import { currentUser } from './auth.js';
import { route, match, parseLocation, navigate, start, link, safePath } from './router.js';
import { html, mount, spinner, errorBox, avatar, toast } from './ui.js';
import * as auth from './pages/auth.js';
import { home } from './pages/catalogue.js';
import { course } from './pages/course.js';
import { dashboard, editProfile } from './pages/dashboard.js';
import { instructorProfile, studentProfile } from './pages/profiles.js';
import * as teach from './pages/instructor.js';
import { inbox, room } from './pages/chat.js';

// ----------------------------------------------------------------------------- routes
// `auth: true` needs any login, `role` needs that user_cat; guests are sent to /login?next=
route('/', home);
route('/courses/:id', course);
route('/instructors/:username', instructorProfile);
route('/students/:username', studentProfile, { auth: true });

route('/login', auth.login, { guest: true });
route('/register', auth.register, { guest: true });
route('/activate', auth.activate, { guest: true });
route('/forgot', auth.forgot, { guest: true });
route('/reset', auth.reset, { guest: true });
route('/logout', auth.logout);

route('/me', dashboard, { auth: true });
route('/me/edit', editProfile, { auth: true });

route('/messages', inbox, { auth: true });
route('/messages/:tutor/:learner', room, { auth: true });

route('/teach', teach.teach, { role: 'instructor' });
route('/teach/courses/new', teach.newCourse, { role: 'instructor' });
route('/teach/courses/:id', teach.manageCourse, { role: 'instructor' });
route('/teach/learners', teach.learners, { role: 'instructor' });
route('/teach/blocks', teach.blocks, { role: 'instructor' });

// ----------------------------------------------------------------------------- nav
function renderNav() {
  const user = currentUser();
  const { path } = parseLocation();
  const active = (prefix) => (path === prefix || path.startsWith(prefix + '/') ? 'active' : '');
  mount(document.getElementById('nav'), html`
    <a class="brand" href="${link('/')}">ELEARN</a>
    <button class="burger" aria-label="menu" aria-expanded="false">☰</button>
    <div class="links">
      <a class="${path === '/' ? 'active' : ''}" href="${link('/')}">Courses</a>
      ${user ? html`
        ${user.user_cat === 'instructor' ? html`<a class="${active('/teach')}" href="${link('/teach')}">Teach</a>` : ''}
        <a class="${active('/messages')}" href="${link('/messages')}">Messages</a>
        <a class="${active('/me')} user" href="${link('/me')}">${avatar(user, 'xs')} ${user.USER_NAME}</a>
        <a href="${link('/logout')}">Log out</a>
      ` : html`
        <a class="${active('/login')}" href="${link('/login')}">Log in</a>
        <a class="btn primary small" href="${link('/register')}">Sign up</a>
      `}
    </div>`);
  const nav = document.getElementById('nav');
  nav.querySelector('.burger').addEventListener('click', (e) => {
    const open = nav.classList.toggle('open');
    e.currentTarget.setAttribute('aria-expanded', String(open));
  });
}

// ----------------------------------------------------------------------------- dispatch
let cleanup = null;
const app = document.getElementById('app');

async function dispatch() {
  if (cleanup) { try { cleanup(); } catch { /* page already gone */ } cleanup = null; }
  document.getElementById('nav').classList.remove('open');
  renderNav();

  const { path, query, search } = parseLocation();
  const found = match(path);
  if (!found) {
    mount(app, html`<section class="narrow center"><h1>Page not found</h1>
      <p class="muted">${path}</p><a class="btn" href="${link('/')}">Back to courses</a></section>`);
    return;
  }
  const { route: r, params } = found;
  const user = currentUser();

  if ((r.auth || r.role) && !user) {
    navigate(link('/login', { next: path + (search ? '?' + search : '') }).slice(1), { replace: true });
    return;
  }
  if (r.role && user.user_cat !== r.role) {
    mount(app, html`<section class="narrow center"><h1>Not for your account</h1>
      <p class="muted">This page is only for ${r.role === 'instructor' ? 'tutors' : 'learners'}.</p>
      <a class="btn" href="${link('/me')}">Go to your dashboard</a></section>`);
    return;
  }
  if (r.guest && user) {
    navigate(safePath(query.next), { replace: true });
    return;
  }

  window.scrollTo(0, 0);
  mount(app, spinner());
  try {
    const result = await r.handler({ el: app, params, query, user });
    if (typeof result === 'function') cleanup = result;
  } catch (err) {
    mount(app, errorBox(err));
  }
}

// a 401 from any call means the token is gone or expired: back to login, keeping the target
window.addEventListener('elearn:unauthorized', () => {
  renderNav();
  const { path, search } = parseLocation();
  toast('Your session has expired. Please log in again.', 'error', 6000);
  navigate(link('/login', { next: path + (search ? '?' + search : '') }).slice(1), { replace: true });
});
window.addEventListener('elearn:session', renderNav);

start(dispatch);
