# TrustVault

## Secure Document Sharing Platform with a Real Audit Trail

TrustVault is a Flask-based web application designed to securely upload, manage, search, and share documents. It uses role-based access control, document-specific permissions, private cloud storage, and audit logging to protect private documents.

**Live Application:** https://trustvault-7z5w.onrender.com

**GitHub Repository:** https://github.com/yadavallimaheswari3/TrustVault

---

## Features

- User registration, login, and logout.
- Three roles: Admin, Owner, and Viewer.
- Secure document upload and download.
- Document metadata editing and deletion.
- Document-specific Read and Edit permissions.
- Owners can grant and revoke document access.
- Search documents using available filters.
- Admin dashboard for user and document statistics.
- Audit logs for important activities and denied access attempts.
- Audit log integrity verification using HMAC-SHA256 hash chaining.
- Upload validation using allowed extensions and file-content checks.
- Persistent document file storage using a private Supabase Storage bucket.

## Technology Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Flask-Migrate
- SQLite for local development
- PostgreSQL through psycopg for production
- Neon PostgreSQL for production database hosting
- Supabase Storage for persistent document files
- Pytest
- Gunicorn
- Render for application hosting

## User Roles and Permissions

| Feature | Admin | Owner | Viewer |
|---|---|---|---|
| Admin dashboard | Yes | No | No |
| Manage users and roles | Yes | No | No |
| View audit logs | Yes | No | No |
| Upload documents | No | Yes | No |
| Manage own documents | No | Yes | No |
| Grant/revoke access to own documents | No | Yes | No |
| Access documents shared with them | No automatic access | Yes, own documents | Yes, with permission |

### Document Permissions

- **Read:** Allows an authorized user to view and download a shared document.
- **Edit:** Allows an authorized user to view, download, and edit document metadata.
- Document owners retain access to their own documents.
- Admin status does not automatically grant access to private documents.

Authorization is checked on the server for protected operations. Removing a permission affects subsequent access requests.

## Security

### Authentication and Authorization

- Passwords are stored as password hashes, not plain text.
- Login is required for protected dashboard and document operations.
- Role and document ownership checks are performed on the server.
- Document permissions are checked against the database.
- Revoked permissions prevent subsequent unauthorized document requests.

### File Upload Validation

- Maximum file size: 10 MB.
- Allowed extensions: PDF, DOC, DOCX, TXT, PNG, JPG, and JPEG.
- Uploaded content is checked against the expected file format.
- Filenames are sanitized before processing.

### Persistent Document Storage

- Document files are stored in a private Supabase Storage bucket named `trustvault-documents`.
- The bucket is not publicly accessible.
- Document metadata and permission records are stored in PostgreSQL in production.
- The application uses server-side Supabase credentials to access the private bucket.
- Users must pass application authorization checks before document downloads.
- The Supabase secret key must never be exposed in frontend code or committed to Git.

### Audit Logging

Important activities are recorded with information such as the actor, action, outcome, timestamp, and available request details.

The audit log integrity mechanism uses HMAC-SHA256 hashes linked through previous-event hashes. Automated tests check valid chains and detect modified event details or broken links.

**Important limitation:** Historical audit entries created before hash protection was introduced are legacy entries and are not cryptographically verified. Hash protection does not replace an independently stored, immutable audit backup.

## Installation and Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yadavallimaheswari3/TrustVault.git
cd TrustVault
```

### 2. Create and Activate a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Configure the required values in `.env`:

```env
SECRET_KEY=replace-with-a-long-random-secret
FLASK_DEBUG=1

SUPABASE_URL=your-supabase-project-url
SUPABASE_SECRET_KEY=your-supabase-secret-key
SUPABASE_BUCKET=trustvault-documents
```

For production, configure `DATABASE_URL` with the Neon PostgreSQL connection string.

For local document upload and download, configure the Supabase storage variables and create the private `trustvault-documents` bucket in Supabase.

Keep `.env` private. Never commit real secret keys, database passwords, or credentials to Git.

Use `FLASK_DEBUG=1` only for local development. Disable debug mode in production.

### 5. Apply Database Migrations

```powershell
flask --app run.py db upgrade
```

### 6. Create User Accounts

Create the first Admin account:

```powershell
python admin.py
```

Create an Owner account:

```powershell
python owner.py
```

New users registered through the application receive the default Viewer role.

The account creation scripts securely request passwords and require a minimum of 12 characters. The Admin script prevents creating another Admin if one already exists.

### 7. Start the Application

```powershell
python run.py
```

Open:

http://127.0.0.1:5000

## Production Deployment

The application is deployed on Render.

- **Application hosting:** Render
- **Production database:** Neon PostgreSQL
- **Document storage:** Supabase Storage
- **Document bucket:** `trustvault-documents` (private)

Configure these environment variables in the Render service:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask application secret |
| `FLASK_DEBUG` | Set to `0` in production |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SECRET_KEY` | Server-side Supabase secret key |
| `SUPABASE_BUCKET` | `trustvault-documents` |

The application applies database migrations during deployment.

The deployed application uses HTTPS through its Render URL. Additional deployment hardening remains a future improvement.

## Demo Accounts

The following dedicated demo accounts are provided for project evaluation.

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | Admin@123456789 |
| Owner | owner@example.com | Owner@123456789 |
| Viewer | viewer@example.com | Viewer@123456789 |

**Live Application:** https://trustvault-7z5w.onrender.com

These accounts are intended only for project evaluation and contain test data. Do not use these passwords for personal accounts or any other service. These credentials are publicly visible in this repository.

## Automated Tests

Run the complete test suite:

```powershell
python -m pytest -q
```

**Latest verified test result: 61 passed.**

The tests cover application basics, registration, login, roles, document operations, permissions, revoked access, upload validation, and audit integrity.

## Application Routes and Access Control

| Method | Endpoint | Access |
|---|---|---|
| GET, POST | `/register` | Public registration |
| GET, POST | `/login` | Public login |
| POST | `/logout` | Authenticated user |
| GET | `/` | Home page |
| GET | `/health` | Public health check |
| GET | `/static/<path:filename>` | Static files |
| GET | `/admin/dashboard` | Admin |
| GET | `/admin/users` | Admin |
| POST | `/admin/users/<user_id>/role` | Admin |
| GET | `/admin/audit-logs` | Admin |
| GET | `/admin/audit-logs/page` | Admin |
| POST | `/documents/upload` | Owner |
| GET | `/documents/<document_id>/download` | Owner or user with Read/Edit permission |
| GET | `/documents/search` | Authenticated user; results limited by access |
| PATCH | `/documents/<document_id>` | Owner or user with Edit permission |
| DELETE | `/documents/<document_id>` | Owner |
| POST | `/documents/<document_id>/permissions` | Document owner |
| DELETE | `/documents/<document_id>/permissions/<user_id>` | Document owner |

Unauthorized requests to protected operations are rejected by server-side checks.

For detailed endpoint documentation, including permission requirements, see `API.md`.

## Threat Model

See [THREATS.md](THREATS.md) for threat scenarios, security controls, testing approach, and accepted limitations.

## AI Development Log

See [PROMPTS.md](PROMPTS.md) for the development prompt log, problems identified, fixes, and testing history.

## Project Limitations and Future Improvements

Potential future improvements include:

- Multi-factor authentication.
- Login rate limiting.
- Malware scanning for uploaded files.
- Additional application-managed encryption at rest.
- External immutable audit-log backups and checkpoints.
- Additional production deployment hardening.
- Backup and recovery procedures.

## Project Status

TrustVault is deployed and its main document-sharing workflow has been manually verified in production.

Verified live operations include:

- Document upload.
- Authorized document download.
- Permission revocation.
- Rejection of revoked-user direct download requests.
- Admin audit log visibility.

The latest local automated test run passed 61 tests.

## Repository

https://github.com/yadavallimaheswari3/TrustVault