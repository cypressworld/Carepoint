# CarePoint Clinic Management

A beginner-friendly Flask clinic management project with separate patient, doctor, and administrator workflows. It demonstrates server-side authorization, SQLAlchemy models and migrations, form validation, appointment scheduling, patient intake, and appointment communication.

> **Learning project:** This app is not a medical device or production-ready electronic health record. Do not use it to store real patient data. Keyword flags are simple text matches for human review, not clinical assessments or emergency monitoring.

## Features

- Public registration creates patient accounts only.
- Login uses password hashes and database-backed role checks.
- Patients can view their appointments, request a future appointment, and submit a care intake with symptoms and previous illness.
- Intake can suggest a doctor when a patient selects a matching specialty. The suggestion is not a diagnosis or automatic assignment.
- Patients and their assigned doctors can exchange messages on an appointment.
- Authorized administrators can manage doctors and specialties, review appointments, and review communications.
- Administrators can suspend or restore doctors. Suspension prevents login and new bookings while keeping the doctor's records and existing appointments.
- Configured communication keywords flag a message for human review. A flag does not automatically penalize a user.
- Appointment requests reject past dates and exact date/time conflicts for either the doctor or patient.
- Database changes provide explicit success or failure feedback; failed commits are rolled back and logged.
- Automated tests cover authentication, authorization, booking, communication, and administration.

## Requirements

- Windows with PowerShell (commands below are PowerShell examples)
- Python 3.10 or newer
- XAMPP with its MySQL service running
- A MySQL database named `carepoint`

## Setup

Open PowerShell in the project folder:

```powershell
cd "C:\path\to\clinic-management"
py -m venv venv
.\venv\Scripts\Activate.ps1
Copy-Item .env.example .env
python -m pip install -r requirements.txt
```

If PowerShell says script execution is disabled, use the venv's Python directly instead of activating it:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start **MySQL** in the XAMPP Control Panel. In phpMyAdmin, create a database named `carepoint`. The default connection in `.env.example` assumes `localhost:3306`, the `root` account, and no password. Edit `DATABASE_URL` in `.env` if your MySQL credentials, host, or port differ:

```dotenv
DATABASE_URL=mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE?charset=utf8mb4
```

URL-encode special characters in a username or password before putting them in the connection URL. Set a unique `SECRET_KEY` in `.env`. Never commit `.env` or put real credentials in source code.

## Create or update the database schema

With the project venv active and MySQL running:

```powershell
flask --app run.py db upgrade
```

Or call Flask through the project venv explicitly:

```powershell
.\venv\Scripts\python.exe -m flask --app run.py db upgrade
```

When models change, generate and review a migration, then apply it:

```powershell
flask --app run.py db migrate -m "Describe the schema change"
flask --app run.py db upgrade
```

Do not delete the database to update its schema. Migrations preserve existing data as the schema evolves.

## Create the first administrator

Admin accounts cannot be created through public registration. Add temporary bootstrap values to `.env` (use a unique password of at least 12 characters):

```dotenv
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=replace-with-a-unique-password-of-12-or-more-characters
```

Run:

```powershell
python seed_admin.py
```

After the script reports that the administrator was created, remove `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`. Log in at `http://127.0.0.1:5000/auth/login`. Administrators create doctor accounts from the **Doctors** page; the initial doctor password is set during creation.

## Run the application

```powershell
python run.py
```

Open `http://127.0.0.1:5000/`. Register a patient account, then log in. Use the bootstrap administrator account to create specialties and doctor accounts.

## Run tests

```powershell
python -m pytest -q
```

Tests use a separate in-memory SQLite database; they do not modify the XAMPP MySQL database.

## Main routes

| Area | Routes |
| --- | --- |
| Public/authentication | `/`, `/auth/register`, `/auth/login`, `/auth/logout` |
| Patient | `/patient/dashboard`, `/patient/profile`, `/patient/appointments/new`, `/communication/intake` |
| Doctor | `/doctor/dashboard` |
| Appointment chat | `/communication/appointments/<id>` |
| Administrator | `/admin/dashboard`, `/admin/doctors`, `/admin/specialties`, `/admin/patients`, `/admin/appointments`, `/communication/admin` |

Protected actions use server-side role checks; hiding a link in the page is not considered authorization. Patient and doctor chat access is also restricted to the appointment participants. Administrator chat review is available to authorized admins.

## Project layout

```text
app/
  auth/             Registration, login, logout, and role checks
  admin/            Doctor, specialty, patient, and appointment administration
  communication/    Intake, appointment chat, and admin review
  doctor/           Doctor dashboard and assigned appointment actions
  main/             Public landing page
  patient/          Patient dashboard, profile, and appointment booking
  models/           SQLAlchemy database models
  templates/        Jinja pages organized by feature
  static/            CSS and static assets
migrations/          Alembic/Flask-Migrate schema history
tests/               Automated tests using an isolated test database
config.py            Environment-based settings
run.py               Flask application entry point
seed_admin.py        Out-of-band first administrator setup
lesson2.text         Beginner step-by-step development lesson
```

## Learning guide

See [lesson2.text](lesson2.text) for a beginner-friendly, step-by-step explanation of how to build a similar Flask project manually, including setup, database design, routes, authentication, validation, migrations, testing, and practice tasks.

## Safety and limitations

- This learning application has not been assessed for medical, privacy, or regulatory compliance. Do not use real patient data or deploy it for clinical care without a qualified security, privacy, legal, and clinical review.
- The specialty suggestion is a simple directory lookup—not symptom diagnosis, medical triage, or an automated referral.
- Keyword-based flags can produce false positives and false negatives. Administrators must review them; the app does not provide emergency response or automatic account discipline.
- Use HTTPS, a secure production secret, least-privilege database credentials, backups, and a production-grade deployment server before any real deployment.
