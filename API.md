# TrustVault API Documentation

## Overview

TrustVault is a Flask-based secure document-sharing application. It uses session-based authentication, role-based access control and document-level permissions.

## Authentication Routes

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET, POST | `/register` | Public | Register an account |
| GET, POST | `/login` | Public | Log in |
| POST | `/logout` | Authenticated | Log out |

## Main Routes

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/` | Public | Home page |
| GET | `/health` | Public | Health check |
| GET | `/static/<path:filename>` | Public | Serve static files |

## Document Routes

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/documents/upload` | Owner | Upload a document |
| GET | `/documents/<int:document_id>/download` | Owner or permitted viewer | Download a document |
| GET | `/documents/search` | Authenticated | Search accessible documents |
| PATCH | `/documents/<int:document_id>` | Owner or Edit permission | Edit document metadata |
| DELETE | `/documents/<int:document_id>` | Owner | Delete a document |

## Permission Routes

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/documents/<int:document_id>/permissions` | Document owner | Grant document access |
| DELETE | `/documents/<int:document_id>/permissions/<int:user_id>` | Document owner | Revoke document access |

## Admin Routes

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/admin/dashboard` | Admin | View administration dashboard |
| GET | `/admin/users` | Admin | Manage users |
| POST | `/admin/users/<int:user_id>/role` | Admin | Change a user's role |
| GET | `/admin/audit-logs` | Admin | View audit logs |
| GET | `/admin/audit-logs/page` | Admin | Load audit log page data |

## Document Permission Rules

- **Owner:** Can view, download, edit metadata, delete, grant access and revoke access to their own documents.
- **Viewer with Read permission:** Can view and download shared documents.
- **Viewer with Edit permission:** Can view, download and edit document metadata.
- **Admin:** Can manage users and view audit logs. Admin status alone does not grant access to private documents.

## Security

- Protected routes require authentication.
- Document access is checked on the server.
- Revoked permissions are checked on subsequent requests.
- Unauthorized document requests are rejected.
- Document activities and permission changes are recorded in audit logs.
- Uploaded files are stored in a private Supabase Storage bucket.

## Notes

This document lists the registered Flask routes and their intended access levels. Request fields, response formats and error codes should be confirmed against the route implementations.