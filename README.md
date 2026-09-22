# E-Learning Platform

A multi-role learning platform: a Django 5 JSON API served over ASGI, and a single-page
frontend written in plain HTML, CSS and JavaScript with no framework and no build step.
Course delivery, tutor and learner dashboards, email-driven account workflows and a
real-time learner↔tutor chat.

```bash
cp .env.example .env     # then set DJANGO_SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

Then open <http://localhost:8080/>.

---

## What it does

**Learners**
- Register with an emailed activation code; an inactive account is told to activate rather than
  just being refused
- Self-service password reset
- Browse and search the catalogue, enrol, watch lectures and download lecture attachments
- Rate a course (1–5) and write one review, both editable and removable
- Dashboard of enrolled courses and a status shown on their public page
- Message the tutor of any course they are enrolled in
- Appeal by email when a tutor has blocked them

**Tutors**
- Create courses as drafts, publish them, edit or delete them
- Add, edit and remove lectures with a video and an optional attachment
- See who is enrolled, per course and across all courses
- Block and unblock learners; a block closes the chat and hides the course immediately
- Email every learner on a course
- Public profile with their published courses and a status

**Real time**
- One private room per (learner, tutor) pair over websockets, with REST polling as a fallback
  when the socket cannot be opened

---

## Architecture

```
ELEARN_BACKEND/           Django 5, API only — no templates, no server-rendered pages
├── ELEARN_BACKEND/       settings, ASGI entrypoint, celery config, /api/v1/ route table
├── HOME_AREA/            auth, JWT, password hashing, catalogue, peer chat + its consumer
├── INSTRUCTOR/           tutor models, endpoints and the CSV seed command
└── STUDENT/              learner models and endpoints
ELEARN_FRONTEND/          the SPA (plain HTML + JS) and the nginx image that serves it
docker-compose.yml        postgres, redis, web, worker, beat, frontend
```

| Concern | Choice |
|---|---|
| API | Django 5.0 + Django REST Framework 3.15 |
| Async / real-time | Django Channels 4.1 on Daphne (ASGI), Redis channel layer |
| Background work | Celery 5.4 with Celery Beat |
| Database | PostgreSQL 16 (SQLite for a quick local run) |
| Cache / broker | Redis 7 |
| Frontend | Hand-written ES modules, hash router, no framework, no build step |
| Edge | nginx — serves the SPA and proxies the API, websockets, media and static |
| Docs | OpenAPI 3 via drf-spectacular, Swagger UI at `/api/schema/swagger-ui/` |

One process model handles both HTTP and websockets, so real-time features need no second
service. nginx puts the SPA and the API on a single origin, which means the browser never
makes a cross-origin request and CORS is not involved at all.

---

## Running it

### With docker compose (recommended)

```bash
cp .env.example .env
# fill in DJANGO_SECRET_KEY and POSTGRES_PASSWORD, and set DJANGO_DB_ENGINE=postgres
docker compose up --build
```

| URL | What |
|---|---|
| <http://localhost:8080/> | the app |
| <http://localhost:8080/api/schema/swagger-ui/> | interactive API docs |
| <http://localhost:8080/admin/> | Django admin |

Everything goes through nginx on port 8080; the backend is not published directly.
The `web` container runs the migrations and `collectstatic` on start; `worker` and `beat`
wait for it and skip both (`RUN_MIGRATIONS=0`).

Useful follow-ups:

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py LoadData      # seed demo tutors, learners, courses
docker compose exec web python manage.py test          # run the test suite
docker compose down -v                                 # stop and wipe the volumes
```

Without SMTP credentials, activation and reset codes are printed to the log instead of
emailed — read them with `docker compose logs -f web`.

### Accounts and roles

There are two separate populations, and they log in in different places.

| Role | Table | Signs in at | Can |
|---|---|---|---|
| Learner | `STUDENT` | the SPA, "Learner" | enrol, watch, rate, review, message their tutors |
| Tutor | `INSTRUCTOR` | the SPA, "Tutor" | own courses and lectures, see and block their learners |
| Moderator | `auth.User` + `Moderators` group | `/admin/` | take down content, see enrolments, block on a tutor's behalf |
| Admin | `auth.User` superuser | `/admin/` | everything |

Learners and tutors are **not** `django.contrib.auth` users and can never reach the admin
site — `is_staff` is hard-coded `False` on both models, so a platform login is refused at
`/admin/` even if an address happens to collide with a staff username.

A moderator moderates content and conduct, not accounts. The exact permission set is one
list in [`HOME_AREA/staff.py`](ELEARN_BACKEND/HOME_AREA/staff.py); what it deliberately
withholds is the interesting part:

- no access to `auth.User` or `auth.Group`, so a moderator cannot create staff or grant
  permissions — not even to themselves
- no add or delete on `STUDENT` / `INSTRUCTOR`: they can suspend an account (`Isactive`),
  not create or erase one
- the `PASSWORD` field is hidden from them on both models, so they cannot set a password
  and sign in as that person. Only a superuser sees it, and typing into it stores a hash.

Create the accounts and sync the group:

```bash
docker compose exec web python manage.py SeedStaff
```

It is idempotent: run it again after editing `MODERATOR_PERMISSIONS` and the group catches
up, including permissions removed from the list. `--moderators N` changes how many are
created, and `--promote <username>` makes an existing user a moderator.

New accounts are created with an unusable password, because `SeedStaff` deliberately does
not deal in credentials — `DumpUsers` does.

### Getting the passwords out

```bash
docker compose exec web python manage.py DumpUsers --out /app/users.txt
docker compose cp web:/app/users.txt ./users.txt
```

`users.txt` lists every account — admins, moderators, tutors and learners — with a password
that works. Passwords are stored as hashes, so:

- learners and tutors seeded from `INSTRUCTOR/CSVs` are reported with their original
  password, verified against the stored hash first (`seeded`)
- for anything else there is nothing to recover, so a new password is generated and saved
  (`reset`). Any API token held by those accounts stops working. `--no-reset` lists them as
  unknown instead of touching them.

The file is plaintext credentials. It is gitignored, it must never be written under
`MEDIA_ROOT` (nginx serves that directory), and it is a development convenience — for a real
deployment, create the superuser with `createsuperuser` and let people set their own
passwords.

### Without docker

```bash
cd ELEARN_BACKEND
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export DJANGO_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key as k; print(k())")
export DJANGO_DEBUG=True
python manage.py migrate
python manage.py runserver
```

That uses SQLite and expects Redis on `127.0.0.1:6379` for the cache, the channel layer and
celery. Serve the SPA from the same origin, or from its own and set `API_BASE` in
[`ELEARN_FRONTEND/config.js`](ELEARN_FRONTEND/config.js) plus `CORS_ALLOWED_ORIGINS` on the
backend. See [`ELEARN_FRONTEND/README.md`](ELEARN_FRONTEND/README.md).

```bash
celery -A ELEARN_BACKEND worker -l info
celery -A ELEARN_BACKEND beat -l info
```

---

## Configuration

Every environment-specific setting is read from the environment; nothing secret is committed.
Copy `.env.example` to `.env` and fill it in.

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | **Required.** Signs sessions *and* the API tokens |
| `DJANGO_DEBUG` | `True` in development; defaults to `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Browser-visible origins, needed for admin logins behind nginx |
| `DJANGO_SECURE_SSL` | `True` once TLS is terminated in front: turns on the secure-cookie and redirect settings |
| `DJANGO_DB_ENGINE` | `postgres` or `sqlite` |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT` | Postgres connection |
| `REDIS_URL` | One Redis server; db 0 is celery, 1 the cache, 2 the channel layer |
| `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP for activation codes and resets. Gmail needs an App Password. Empty user ⇒ codes go to the log |
| `API_TOKEN_MAX_AGE` | Seconds a login token stays valid; defaults to 7 days |
| `THROTTLE_LOGIN` / `THROTTLE_REGISTER` / `THROTTLE_CODE` | Per-IP rate limits on the unauthenticated auth endpoints |
| `CORS_ALLOWED_ORIGINS` | Only when the SPA is on another origin (needs `django-cors-headers`) |
| `FRONTEND_PORT` | Host port compose publishes the app on (default 8080) |

---

## Security

- **Passwords are hashed** with Django's PBKDF2 hasher ([`HOME_AREA/passwords.py`](ELEARN_BACKEND/HOME_AREA/passwords.py)).
  Registration, password reset, the seed command and the admin all go through it, and the
  auth backends compare against the hash. Earlier versions of this project stored passwords
  as plaintext; `STUDENT/migrations/0002_hash_passwords.py` and its `INSTRUCTOR` twin widen
  the column and hash existing rows in place, so nobody's password changes.
- **Tokens are stateless and header-only.** No session cookie is set for the SPA, so there is
  no CSRF surface on the API. A token carries a fingerprint of the stored password hash, so
  changing a password invalidates every token issued before it.
- **Rate limits** on login, registration, activation and password reset keep the six-digit
  codes out of brute-force range.
- **Password reset does not leak who has an account**: the answer is identical whether or not
  the address is registered.
- **Uploads are gated.** Lecture video and attachment URLs are only serialised for the course
  owner and for enrolled, unblocked learners.
- **Chat access is one rule in one place** ([`HOME_AREA/access.py`](ELEARN_BACKEND/HOME_AREA/access.py)),
  used by both the HTTP view and the websocket consumer, and re-checked on every message so a
  block or a drop takes effect immediately.
- **The SPA escapes every interpolated value** in its `html` tagged template, so course names,
  reviews and chat messages cannot inject markup.
- **The back office is a separate population.** Learners and tutors cannot reach `/admin/`,
  and moderators get a permission set that excludes accounts, passwords and permissions
  (see *Accounts and roles*).

Known limitations: the JWT is kept in `localStorage`, which is the usual trade-off for a
header-only SPA; the websocket takes its token in the query string, so it can appear in
proxy logs; and activation codes have a rate limit but no expiry.

---

## REST API

Everything the app does is `/api/v1/`. Interactive docs at `/api/schema/swagger-ui/`
(or `/api/schema/redoc/`), raw OpenAPI at `/api/schema/`. Route table:
[`ELEARN_BACKEND/ELEARN_BACKEND/api_urls.py`](ELEARN_BACKEND/ELEARN_BACKEND/api_urls.py).

### Authentication

`POST /api/v1/auth/login/` with `{"user_type": "student" | "instructor", "EMAIL", "PASSWORD"}`
returns `{"token", "expires_in", "user"}`. The token is an HS256 JWT (claims `sub`, `cat`,
`iat`, `exp`, `pw`) signed with `SECRET_KEY` — no token table. Login sets **no cookie**; the
client keeps the token and sends it on every call:

```
Authorization: Bearer <token>
```

Websockets take the same token as a query string:
`ws://host/ws/peerchat/<tutor>/<learner>/?token=<token>`.
An inactive account answers `403 {"Isactive": false}` so the client can route to the
activation screen. Logging out is the client discarding the token (`auth/logout/` exists for
symmetry only).

### Endpoints

| Area | Endpoint | Methods |
|---|---|---|
| Auth | `auth/register/student/`, `auth/register/instructor/` (multipart) | POST |
| | `auth/login/`, `auth/logout/`, `auth/activate/` | POST |
| | `auth/password/forgot/`, `auth/password/reset/` | POST |
| Me | `me/` profile (multipart for `PICTURE`) | GET PATCH DELETE |
| | `me/status/` dashboard status, `me/courses/` enrolled / owned courses | GET PUT DELETE / GET |
| Catalogue | `courses/?search=&instructor=&page=` published courses with rating summary | GET |
| | `courses/{id}/` detail with `viewer` flags (`enrolled`, `blocked`, `is_owner`, `can_watch`) | GET |
| | `courses/{id}/lectures/` media urls (enrolled or owner), `reviews/`, `ratings/` | GET |
| Profiles | `students/{username}/`, `instructors/{username}/` | GET |
| Student | `student/courses/{id}/enroll/` | POST DELETE |
| | `student/courses/{id}/review/`, `student/courses/{id}/rating/` (one per learner, PUT upserts) | GET PUT DELETE |
| | `student/courses/{id}/appeal/` ask a tutor to lift a block | POST |
| Instructor | `instructor/courses/` (multipart `COURSE_NAME`, `COVER_PHOTO`, `IsDraft`) | GET POST |
| | `instructor/courses/{id}/`, `.../publish/`, `.../notify/`, `.../learners/` | GET PATCH PUT DELETE / POST |
| | `instructor/courses/{id}/lectures/`, `.../lectures/{id}/` (multipart `NAME`, `VIDEO`, `ADDITIONAL_FILES`) | CRUD |
| | `instructor/learners/` grouped by course, `instructor/blocks/`, `instructor/blocks/{username}/` | GET / GET POST / DELETE |
| Peer chat | `peer-chats/` inbox, `peer-chats/{tutor}/{learner}/?limit=20&after=<id>` last N messages, oldest first | GET / GET POST |

Field names in the JSON are the model column names (`COURSE_NAME`, `COVER_PHOTO`, `IsDraft`, …).
List endpoints are paginated (`count`, `next`, `previous`, `results`; `page_size` up to 100).

### Peer chat

1. `GET peer-chats/` for the inbox, `GET peer-chats/{tutor}/{learner}/` for the last 20 messages.
2. Open `ws://host/ws/peerchat/{tutor}/{learner}/?token=<jwt>` and send `{"message": "..."}`;
   the server saves it from the authenticated connection — never from anything the client
   claims — and every party in the room receives
   `{"message", "userName", "userCat", "timeStamp"}`.
3. If the socket cannot be opened the client falls back to `POST` plus polling with `?after=<id>`.

---

## Frontend

[`ELEARN_FRONTEND/`](ELEARN_FRONTEND/) is the whole user interface: hash-routed ES modules,
no framework, no `package.json`, no build step. It covers every endpoint above. Its own
[README](ELEARN_FRONTEND/README.md) has the file-by-file map and the route table.

---

## Tests

```bash
docker compose exec web python manage.py test          # or: python manage.py test
```

[`HOME_AREA/tests_api.py`](ELEARN_BACKEND/HOME_AREA/tests_api.py) covers the API surface:
auth and token behaviour, password hashing, draft visibility, media gating, enrolment,
reviews and ratings, tutor course and lecture management, blocks, and peer-chat access
control. [`HOME_AREA/tests_staff.py`](ELEARN_BACKEND/HOME_AREA/tests_staff.py) covers the
back-office boundary: what a moderator can reach, what they cannot, and that a learner or
tutor can never log into the admin. Email and the channel layer are stubbed, so no SMTP or
broker is needed.

---

## Status

Built as a solo project. The Django template pages the project started as have been removed:
the SPA is the only interface, and the server is an API. File sharing inside chat is the one
listed feature that is not built.
