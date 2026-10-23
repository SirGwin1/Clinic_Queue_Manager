# Clinic Queue Manager

A Django clinic queue manager for staff, patient records, queue tracking, live notifications, and reports.

## Features
- Role-based access for administrators, receptionists, and doctors.
- Patient registration, record editing, search, and patient detail views.
- Queue operations: add to queue, call next patient, start/complete consultation, no-show, cancel, and requeue.
- Real-time notification updates using Django Channels and WebSockets.
- Dashboard summaries, queue history, audit logs, and CSV export.

## Requirements
- Python 3.11+
- Django 5.1
- SQLite for local development

## Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
```

## Run the app
```bash
python manage.py runserver 127.0.0.1:8000
```

## Run tests
```bash
python manage.py test
```

## Notes
- This app uses an in-memory Channels layer for local development.
- For production, review security, privacy, access control, and backup requirements before using real patient data.
