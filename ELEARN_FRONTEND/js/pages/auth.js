// Account flows. Every one of them maps 1:1 onto /api/v1/auth/*.
import { api, ApiError } from '../api.js';
import { setSession, clearSession } from '../auth.js';
import { navigate, link, safePath } from '../router.js';
import { html, mount, field, roleSelect, onSubmit, jsonFrom, toast, setTitle, PASSWORD_RULE } from '../ui.js';

export function login({ el, query }) {
  setTitle('Log in');
  mount(el, html`<section class="narrow">
    <h1>Welcome back</h1>
    <form id="login" class="card form">
      ${roleSelect('user_type', query.user_type || 'student')}
      ${field({ label: 'Email', name: 'EMAIL', type: 'email', required: true, value: query.email || '' })}
      ${field({ label: 'Password', name: 'PASSWORD', type: 'password', required: true })}
      <p class="form-error"></p>
      <button class="btn primary" type="submit">Log in</button>
      <p class="muted links">
        <a href="${link('/forgot')}">Forgot password?</a> ·
        <a href="${link('/activate')}">Have an activation code?</a> ·
        <a href="${link('/register')}">Create an account</a>
      </p>
    </form>
  </section>`);

  onSubmit(el.querySelector('#login'), async (fd) => {
    const body = jsonFrom(fd);
    try {
      const data = await api.post('auth/login/', body);
      setSession(data.token, data.user);
      window.dispatchEvent(new CustomEvent('elearn:session'));
      toast(`Logged in as ${data.user.USER_NAME}`, 'success');
      navigate(safePath(query.next), { replace: true });
    } catch (err) {
      // the API flags an inactive account explicitly so we can route to activation
      if (err instanceof ApiError && err.status === 403 && err.data && err.data.Isactive === false) {
        toast(err.message, 'info', 6000);
        navigate(link('/activate', { user_type: body.user_type, email: body.EMAIL }).slice(1));
        return;
      }
      throw err;
    }
  });
}

export function register({ el, query }) {
  const role = query.role === 'instructor' ? 'instructor' : 'student';
  setTitle('Sign up');
  mount(el, html`<section class="narrow">
    <h1>Create your account</h1>
    <div class="tabs">
      <a class="${role === 'student' ? 'active' : ''}" href="${link('/register', { role: 'student' })}">Learner</a>
      <a class="${role === 'instructor' ? 'active' : ''}" href="${link('/register', { role: 'instructor' })}">Tutor</a>
    </div>
    <form id="register" class="card form" enctype="multipart/form-data">
      <div class="two">
        ${field({ label: 'First name', name: 'FIRST_NAME', required: true })}
        ${field({ label: 'Last name', name: 'LAST_NAME', required: true })}
      </div>
      ${field({ label: 'Username', name: 'USER_NAME', required: true, max: 50 })}
      ${field({ label: 'Email', name: 'EMAIL', type: 'email', required: true })}
      ${field({ label: 'Phone', name: 'PHONE', type: 'tel', required: true, max: 15 })}
      ${field({ label: 'Password', name: 'PASSWORD', type: 'password', required: true, ...PASSWORD_RULE })}
      ${field({ label: 'Profile picture', name: 'PICTURE', type: 'file', accept: 'image/*',
        required: role === 'instructor', hint: role === 'instructor' ? 'Tutors need a picture' : 'Optional' })}
      <p class="form-error"></p>
      <button class="btn primary" type="submit">Sign up as a ${role === 'instructor' ? 'tutor' : 'learner'}</button>
      <p class="muted links">Already registered? <a href="${link('/login')}">Log in</a></p>
    </form>
  </section>`);

  onSubmit(el.querySelector('#register'), async (fd) => {
    const data = await api.post(`auth/register/${role}/`, fd);
    toast(data.email_sent ? data.detail : 'Account created, but the activation email could not be sent.',
      data.email_sent ? 'success' : 'error', 7000);
    navigate(link('/activate', { user_type: role, email: fd.get('EMAIL') }).slice(1), { replace: true });
  });
}

export function activate({ el, query }) {
  setTitle('Activate account');
  mount(el, html`<section class="narrow">
    <h1>Activate your account</h1>
    <p class="muted">Enter the 6-digit code we emailed you.</p>
    <form id="activate" class="card form">
      ${roleSelect('user_type', query.user_type || 'student')}
      ${field({ label: 'Email', name: 'EMAIL', type: 'email', required: true, value: query.email || '' })}
      ${field({ label: 'Activation code', name: 'ACTIVATION_CODE', required: true, max: 6, placeholder: '123456' })}
      <p class="form-error"></p>
      <button class="btn primary" type="submit">Activate</button>
    </form>
  </section>`);

  onSubmit(el.querySelector('#activate'), async (fd) => {
    const body = jsonFrom(fd);
    const data = await api.post('auth/activate/', body);
    toast(data.detail, 'success');
    navigate(link('/login', { user_type: body.user_type, email: body.EMAIL }).slice(1), { replace: true });
  });
}

export function forgot({ el, query }) {
  setTitle('Reset password');
  mount(el, html`<section class="narrow">
    <h1>Forgot your password?</h1>
    <form id="forgot" class="card form">
      ${roleSelect('user_type', query.user_type || 'student')}
      ${field({ label: 'Email', name: 'EMAIL', type: 'email', required: true, value: query.email || '' })}
      <p class="form-error"></p>
      <button class="btn primary" type="submit">Send reset code</button>
      <p class="muted links">Already have a code? <a href="${link('/reset')}">Reset now</a></p>
    </form>
  </section>`);

  onSubmit(el.querySelector('#forgot'), async (fd) => {
    const body = jsonFrom(fd);
    const data = await api.post('auth/password/forgot/', body);
    toast(data.detail, data.email_sent ? 'success' : 'error');
    navigate(link('/reset', { user_type: body.user_type, email: body.EMAIL }).slice(1), { replace: true });
  });
}

export function reset({ el, query }) {
  setTitle('Reset password');
  mount(el, html`<section class="narrow">
    <h1>Choose a new password</h1>
    <form id="reset" class="card form">
      ${roleSelect('user_type', query.user_type || 'student')}
      ${field({ label: 'Email', name: 'EMAIL', type: 'email', required: true, value: query.email || '' })}
      ${field({ label: 'Reset code', name: 'ACTIVATION_CODE', required: true, max: 6 })}
      ${field({ label: 'New password', name: 'PASSWORD', type: 'password', required: true, ...PASSWORD_RULE })}
      ${field({ label: 'Confirm password', name: 'CONFIRM_PASSWORD', type: 'password', required: true })}
      <p class="form-error"></p>
      <button class="btn primary" type="submit">Reset password</button>
    </form>
  </section>`);

  onSubmit(el.querySelector('#reset'), async (fd) => {
    const body = jsonFrom(fd);
    const data = await api.post('auth/password/reset/', body);
    toast(data.detail, 'success');
    navigate(link('/login', { user_type: body.user_type, email: body.EMAIL }).slice(1), { replace: true });
  });
}

export function logout() {
  // tokens are stateless: forgetting it is the logout. The endpoint is called best-effort only.
  api.post('auth/logout/').catch(() => {});
  clearSession();
  window.dispatchEvent(new CustomEvent('elearn:session'));
  toast('Logged out.');
  navigate('/', { replace: true });
}
