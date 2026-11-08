# TrustVault — Threat Model

## 1. Project Overview

TrustVault is a secure document-sharing application built using Flask.

Its main goal is to ensure that users can access only documents they own or documents explicitly shared with them.

## 2. Important Assets

- User email addresses and password hashes.
- Uploaded documents and their contents.
- Document ownership information.
- Read and edit permissions.
- Audit logs containing user activities and denied access attempts.
- User roles: Admin, Owner, and Viewer.

## 3. Security Threats and Mitigations

| Threat | Security measure |
|---|---|
| Unauthorized document access | Server-side permission checks |
| Viewer attempting to edit documents | Edit permission required |
| Unauthorized document downloads | Access checked before download |
| Unauthorized document deletion | Owner-only deletion |
| Unauthorized permission changes | Document ownership verification |
| Access after permission revocation | Permission checked against current database records |
| Malicious file uploads | File extension and size validation |
| Unauthorized Admin access | Admin role verification |
| Attempts to access another user's documents | Document-level access checks |
| Untraceable security incidents | Audit logging of allowed and denied actions |

## 4. Roles and Access Control

### Admin
- Manages user accounts and roles.
- Views security activity and audit logs.
- Cannot automatically access every private document.

### Owner
- Uploads and manages owned documents.
- Grants and revokes document permissions.
- Can grant Read or Edit access.

### Viewer
- Can access documents only when permission is granted.
- Cannot edit or delete documents without the required authorization.

## 5. Audit Logging

TrustVault records important security events, including:

- Document uploads.
- Document downloads.
- Document edits and deletions.
- Permission grants and revocations.
- Role changes.
- Denied access and unauthorized attempts.

Audit records include available information such as the actor, action, outcome, timestamp, and IP address.

## 6. File Upload Protection

The application uses an allowed file-extension list and a maximum upload size of 10 MB.

Allowed extensions include PDF, DOC, DOCX, TXT, PNG, JPG, and JPEG.

File upload validation is performed on the server.

## 7. Security Limitations and Future Improvements

The following protections require additional implementation or deployment verification:

- Multi-factor authentication.
- Login rate limiting and account lockout.
- Malware scanning for uploaded files.
- Encryption at rest for uploaded documents.
- Tamper-resistant audit log storage.
- Production HTTPS and secure deployment configuration.
- Automated backup and recovery procedures.

These limitations should not be considered implemented until they have been verified.

## 8. Security Testing

The project includes automated tests for authentication, roles, document access, permission management, and denied operations.

At the latest recorded full test run, the test suite reported **57 passed**.

Further security testing is required before final submission.