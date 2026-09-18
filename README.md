# E-Learning Platform

A multi-role learning platform built with Django 5 — course delivery, instructor and student
dashboards, and email-driven account workflows, served over ASGI so real-time features can run
alongside ordinary request/response views.

## What it does

The system separates three audiences into their own Django apps, each with its own views,
templates and permission rules.

**Students**
- Register with an emailed activation code; inactive accounts are blocked at login and
  redirected to the activation page rather than failing silently
- Self-service password reset
- Dashboard of currently enrolled courses
- A status area visible to peers and instructors
- Contact an instructor directly to resolve a mistaken block

**Instructors**
- Dashboard listing their courses with per-course enrolment counts
- Create courses; add, edit and remove lectures
- Browse enrolled students and open individual student accounts
- Block and unblock students
- Post a status visible to their students

**Courses**
- Lecture delivery
- Reviews with aggregate rating breakdown
- Public course detail pages

## Architecture

```
ELEARN_BACKEND/
├── ELEARN_BACKEND/   project settings, ASGI entrypoint, Celery config
├── HOME_AREA/        public pages, auth, activation and password-reset flows
├── INSTRUCTOR/       instructor dashboard, course and lecture management
├── STUDENT/          student dashboard, enrolment, status
└── theme/            Tailwind theme app
```

| Concern | Choice |
|---|---|
| Framework | Django 5.0 |
| Async / real-time | Django Channels 4.1 on Daphne (ASGI) |
| Background work | Celery 5.4 with Celery Beat for scheduled notifications |
| Broker / cache | Redis |
| Styling | Tailwind CSS via `django-tailwind` |
| Database | SQLite in development |

Running under Daphne rather than WSGI means the HTTP views and the Channels consumers share
one process model, so real-time course notifications do not need a second service.

## Running it locally

```bash
git clone https://github.com/ahmadbackend/ELEARN_PLATFORM.git
cd ELEARN_PLATFORM/ELEARN_BACKEND

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env       # then edit it — see Configuration
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Redis must be running for Celery and Channels:

```bash
redis-server
celery -A ELEARN_BACKEND worker -l info
celery -A ELEARN_BACKEND beat -l info
```

## Configuration

Settings are read from the environment — nothing secret is committed. Copy `.env.example`
to `.env` and fill it in:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Required. Generate with `django.core.management.utils.get_random_secret_key()` |
| `DJANGO_DEBUG` | `True` in development; defaults to `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames |
| `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP for activation codes and password resets. Gmail needs an App Password |
| `CELERY_BROKER_URL` | Redis connection string |

## Status

Built as a solo project. The features listed above are implemented and working. Chat
(group, instructor-to-class, and one-to-one with file sharing) and a documented REST API
are designed but not yet built.
