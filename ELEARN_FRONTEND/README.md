# ELEARN frontend

The whole user interface, written in plain HTML, CSS and JavaScript (ES modules).
No framework, no `package.json`, no build step: the folder is served as-is.

## Run it

The usual way is `docker compose up` from the repository root — nginx serves this folder and
proxies `/api/`, `/ws/`, `/media/`, `/static/` and `/admin/` to Django, so the app and the API
share one origin and `API_BASE` can stay empty.

To run it against a backend on a different origin:

1. Set `API_BASE` in [`config.js`](config.js), e.g. `http://127.0.0.1:8000`.
2. Install `django-cors-headers` and put this app's origin in `CORS_ALLOWED_ORIGINS` on the backend.
3. Serve the folder with any static server:

   ```bash
   python -m http.server 5173 --bind localhost
   ```

   and open <http://localhost:5173/>. (`file://` will not work: ES modules need http.)

## How it is put together

| File | Role |
|---|---|
| `index.html` | the only page; everything renders into `<main id="app">` |
| `config.js` | runtime config (backend URL) |
| `js/app.js` | route table, auth guards, top navigation |
| `js/router.js` | hash router (`#/courses/12?page=2`) so no server rewrites are needed |
| `js/api.js` | `fetch` wrapper: `/api/v1/` base, `Authorization: Bearer <jwt>`, DRF error mapping, 401 handling |
| `js/auth.js` | token + profile in `localStorage`; reads `exp` from the JWT payload |
| `js/ui.js` | `html` tagged template (auto-escaping), form helpers, cards, avatars, toasts |
| `js/pages/*.js` | one module per area: auth, catalogue, course, dashboard, profiles, instructor, chat |
| `css/app.css` | the stylesheet (light + dark, respects `prefers-reduced-motion`) |
| `nginx.conf`, `proxy_headers.conf`, `Dockerfile` | the image that serves this folder and fronts Django |

Rules the code follows:

- **Everything interpolated is escaped.** `html\`\`` escapes every value it renders, so course
  names, reviews and chat messages cannot inject markup. Only `raw()` bypasses it, and nothing
  passes user data to it.
- **Auth is header-only.** The JWT from `auth/login/` is sent as `Authorization: Bearer …`;
  `fetch` runs with `credentials: 'omit'` so no cookie is ever attached. A 401 clears the
  session and returns to `#/login?next=…`, and a `next` that is not a path inside this app is
  discarded rather than followed.
- **Chat is the peer-chat websocket.** A room loads the last 20 messages from
  `GET peer-chats/{tutor}/{learner}/`, then opens `ws/peerchat/{tutor}/{learner}/?token=<jwt>`
  and sends `{"message"}` frames. If the socket cannot be opened it falls back to `POST` plus
  polling with `?after=<id>`, and retries the socket every 10 s.
- **Pages clean up after themselves.** A page handler may return a function; the router calls
  it on the way out, which is how the chat room closes its socket and stops its poller.

## Routes

| Hash | Who | Backed by |
|---|---|---|
| `#/` | anyone | `courses/?search=&page=` |
| `#/courses/:id` | anyone (actions need login) | `courses/{id}/`, `…/reviews/`, `student/courses/{id}/{enroll,rating,review,appeal}/` |
| `#/instructors/:username`, `#/students/:username` | anyone / logged in | `instructors/{u}/`, `students/{u}/` |
| `#/login`, `#/register`, `#/activate`, `#/forgot`, `#/reset`, `#/logout` | guests | `auth/*` |
| `#/me`, `#/me/edit` | logged in | `me/`, `me/status/`, `me/courses/` |
| `#/messages`, `#/messages/:tutor/:learner` | logged in | `peer-chats/…` + websocket |
| `#/teach`, `#/teach/courses/new`, `#/teach/courses/:id` | tutors | `instructor/courses/…`, `…/lectures/…`, `…/publish/`, `…/notify/`, `…/learners/` |
| `#/teach/learners`, `#/teach/blocks` | tutors | `instructor/learners/`, `instructor/blocks/…` |
