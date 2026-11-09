# TrustVault API Documentation

## Overview

TrustVault is a Flask-based secure document-sharing application. Its routes use authenticated sessions and server-side role and document-permission checks.

## Authentication

Users must log in before accessing protected routes. The application uses session-based authentication.

## Main Routes

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/` | Public | Home page |
| GET | `/health` | Public | Health check |
| GET | `/documents` | Authenticated | View accessible documents |
| POST | `/documents/upload` | Owner | Upload a document |
| GET | `/documents/<id>/download` | Owner or permitted viewer | Download a document |
| GET | `/documents/search` | Authenticated | Search accessible documents |
| PATCH | `/documents/<id>` | Owner or Edit permission | Update document details |
| DELETE | `/documents/<id>` | Owner | Delete a document |
| POST | `/documents/<id>/permissions` | Owner | Grant document access |
| DELETE | `/documents/<id>/permissions/<user_id>` | Owner | Revoke document access |
| GET | `/admin/dashboard` | Admin | View administration dashboard |
| GET | `/admin/users` | Admin | Manage users |
| GET | `/admin/audit-logs` | Admin | View audit logs |

## Document Permission Rules

- **Owner:** Can view, download, edit metadata, delete, grant access and revoke access to their own documents.
- **Viewer with Read permission:** Can view and download shared documents.
- **Viewer with Edit permission:** Can view, download and edit document metadata.
- **Admin:** Can manage users and view audit logs. Admin status alone does not grant access to private documents.

## Security

- Document permissions are checked on the server.
- Revoked permissions are checked again on subsequent requests.
- Unauthorized document access is rejected.
- Document activities and permission changes are recorded in audit logs.
- Uploaded files are stored in a private Supabase Storage bucket.

## Notes

This document summarizes the main application routes. Exact request fields, response formats and error codes should be checked against the current route implementation.