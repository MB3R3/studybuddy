# StudyBuddy

StudyBuddy is a Django-based study-room platform for collaborative learning. It gives learners a simple place to discover study topics, create public study rooms, and exchange messages with other users.

The application is server-rendered, uses Django's built-in authentication system, and stores data in SQLite. It does not require a separate frontend build or external infrastructure to run locally.

## Overview

StudyBuddy is organised around three core concepts:

- **Topics** group rooms by subject, such as Python, Django, or frontend development.
- **Rooms** are public discussion spaces created by a host and associated with a topic.
- **Messages** are posted inside rooms and form the discussion history.

Users can browse rooms without signing in. Creating rooms, posting messages, and managing content requires an authenticated account.

## Features

- User registration, login, and logout
- Public room discovery and keyword search
- Topic browsing and filtering
- Room creation, editing, and deletion for room hosts
- Room message threads
- Message deletion for message authors
- Public user profiles showing hosted rooms and recent messages
- Recent activity feed across rooms
- Django administration interface
- Automated test coverage for authentication, room management, messaging, profiles, search, and authorization boundaries

## Technology

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Web framework | Django 4.2 |
| Database | SQLite |
| Authentication | Django authentication |
| Frontend | Django templates, HTML, CSS, vanilla JavaScript |

## Architecture

StudyBuddy follows Django's model-template-view pattern:

- Models provide the persistence layer for topics, rooms, and messages.
- Function-based views implement authentication, room management, messaging, profiles, and activity pages.
- Django templates render the user interface.
- Static assets provide styling and client-side behaviour.

### Data model

| Model | Purpose |
|---|---|
| `Topic` | A subject category used to group study rooms |
| `Room` | A public study room with a host, topic, description, and participants |
| `Message` | A message posted by a user inside a room |

## Repository structure

```text
.
|-- backend/
|   |-- manage.py
|   |-- config/        # Django project configuration
|   |-- base/          # Main application (models, views, forms, tests, templates)
|   |-- templates/     # Project-level templates
|   |-- static/        # CSS, JavaScript, and image assets
|   |-- requirements/  # Python dependency manifests
|   `-- db.sqlite3     # Local development database (not committed)
|-- docs/              # Project documentation and audit notes
|-- scripts/           # Reserved for project scripts
|-- .env.example       # Example environment configuration
|-- .gitignore
`-- README.md
```

## Getting started

### Prerequisites

- Python 3.10 or later
- pip
- Git

The project is developed and tested with Python 3.10 and Django 4.2.

### Installation

```powershell
git clone https://github.com/MB3R3/studybuddy.git
cd studybuddy/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/base.txt
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

### Environment configuration

The application reads configuration from environment variables. `.env` files are not loaded automatically, so variables must be set in the active shell or by the deployment environment.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | Development-only fallback | Secret used for cryptographic signing. Set a strong, unique value outside local development. |
| `DEBUG` | `True` | Enables Django debug mode. Set to `False` in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames accepted by Django. |

PowerShell example:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-value"
$env:DEBUG = "True"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"
```

Do not commit secrets or production credentials to the repository.

### Database setup

Apply the existing migrations before starting the application:

```powershell
cd backend
python manage.py migrate
```

To inspect migration state:

```powershell
python manage.py showmigrations
```

The default database is `backend/db.sqlite3`. It is intended for local development and is excluded from version control.

### Running the application

```powershell
cd backend
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser.

To create an administrative account for the Django admin interface:

```powershell
python manage.py createsuperuser
```

The admin interface is available at `http://127.0.0.1:8000/admin/`.

## Testing

Run the automated test suite from the `backend` directory:

```powershell
python manage.py test
```

Run Django's system checks:

```powershell
python manage.py check
```

The test suite uses Django's test database and does not depend on the local SQLite data.

## Access model

StudyBuddy currently uses public study rooms:

- Room listings, room details, topics, profiles, and activity are publicly readable.
- Authentication is required to create rooms and post messages.
- Only a room's host can edit or delete that room.
- Only a message's author can delete that message.
- Posting a message adds the user to the room's participant list.

Private rooms, membership approval, and per-room visibility rules are not currently implemented.

## Security and deployment

The default settings are intended for local development. Before deploying the application:

- Set a strong, unique `SECRET_KEY`.
- Set `DEBUG` to `False`.
- Configure `ALLOWED_HOSTS` for the deployment domain.
- Serve the application over HTTPS.
- Enable secure session and CSRF cookies.
- Use a production-grade database and web server.
- Review Django's deployment checklist for the target environment.

Django's authentication, CSRF protection, password validation, and clickjacking middleware are enabled by default.

## Documentation

Project documentation, audit notes, and planning material are maintained in the `docs/` directory.

## Project status

StudyBuddy is an actively maintained Django application focused on public study-room collaboration. The current implementation prioritises a clear, lightweight experience and a small operational footprint.
