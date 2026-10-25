# StudyBuddy (Chatroom)

A Django-based study room/chat application for collaborative learning. Users can create/join rooms, post messages, filter by topics, and view activity/profiles.

## Technology stack (verified)
- Python 3.10.5
- Django 4.2
- SQLite (db.sqlite3)
- HTML/CSS/JS (static/, templates/)

## Repository layout
`
.
+-- backend/
�   +-- manage.py
�   +-- config/        # Django project (settings/urls/wsgi/asgi)
�   +-- base/          # Main app (models/views/urls/forms/templates)
�   +-- templates/     # Project templates
�   +-- static/        # Static assets
�   +-- db.sqlite3     # Local DB (preserved)
�   +-- requirements/  # base.txt, dev.txt
+-- docs/              # audits/architecture/development/operations/product
+-- scripts/           # reserved
+-- .env.example
+-- .gitignore
`

## Prerequisites
- Python 3.10+ available
- pip

## Local setup
`powershell
# From repo root
cd backend

# Create/activate venv (optional but recommended)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install deps
pip install -r requirements/base.txt
`

## Environment variables
`.env.example` documents the supported variables. The project does not load `.env` automatically; set them in your shell before running Django. Do not commit secrets.

`powershell
$env:SECRET_KEY = "replace-with-a-long-random-value"
$env:DEBUG = "True"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"
`

## Database & migrations
`powershell
cd backend
python manage.py migrate  # (read-only check preferred; existing migrations already applied)
python manage.py showmigrations
`

## Run development server
`powershell
cd backend
python manage.py runserver
`

## Tests
`powershell
cd backend
python manage.py test
`

## Known limitations
- Rooms are public; there is no private-room or access-control system.
- `DEBUG` defaults to `True` for local development.
- A pre-existing model/migration drift remains for `Message.Meta.ordering`.
- Existing tracked pyc/db changes remain uncommitted.

