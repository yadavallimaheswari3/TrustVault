# TrustVault — Threat Model

## 1. Project Overview

TrustVault is a Flask-based secure document-sharing application.

Its security objective is to ensure that users can access only documents they own or documents explicitly shared with them. Authorization is enforced on the server, not merely through interface visibility.

This document describes important assets, possible attackers, threat scenarios, existing security controls, security tests, and accepted limitations.

## 2. Assets to Protect

| Asset | Security importance |
|---|---|
| User accounts | Prevent unauthorized account access |
| Password hashes | Protect stored authentication credentials |
| Uploaded documents | Protect confidentiality and integrity |
| Document ownership | Prevent unauthorized management |
| Document permissions | Prevent unauthorized sharing or access |
| User roles | Prevent privilege escalation |
| Audit logs | Preserve evidence of security-related activity |
| Application secret key | Protect sessions and audit-event signatures |
| Database and uploaded-file storage | Prevent unauthorized modification or deletion |

## 3. Threat Actors

Potential threat actors include:

- An unauthenticated visitor attempting to access protected routes.
- A Viewer attempting to access another user's private documents.
- A user attempting to obtain Owner or Admin privileges.
- A user attempting to change permissions on documents they do not own.
- An attacker uploading a file with misleading content or an unsafe filename.
- A person with unauthorized access to the application server, database, or secret configuration.

## 4. Threat Scenarios and Mitigations

### Threat 1: Unauthorized document access (IDOR)

**Attack:** A user changes a document ID in a URL or request to access another user's private document.

**Impact:** Confidential documents could be exposed.

**Existing controls:**
- Protected document routes require authentication.
- Document access is checked on the server.
- The `can_view_document()` function checks ownership and document-specific permissions.
- Search results are restricted to documents the user is allowed to view.

**Security tests:** Document-route and permission tests verify access restrictions and cross-user isolation.

### Threat 2: Unauthorized document editing

**Attack:** A Viewer or another unauthorized user sends a direct PATCH request instead of using the normal interface.

**Impact:** Document metadata could be changed without permission.

**Existing controls:**
- The edit route checks `can_edit_document()` on the server.
- Owners can edit their own documents.
- Other users require an Edit permission.
- Denied edit attempts are recorded in the audit log.

**Security tests:** Permission and document-route tests cover unauthorized editing.

### Threat 3: Unauthorized document deletion

**Attack:** A user sends a DELETE request for a document they do not own.

**Impact:** Important documents could be deleted.

**Existing controls:**
- The delete route verifies document ownership.
- Only the owner can delete the document.
- Denied deletion attempts are recorded.

**Security tests:** Document-route tests cover deletion authorization.

### Threat 4: Unauthorized permission changes

**Attack:** A Viewer or another user attempts to grant or revoke access to someone else's document.

**Impact:** Private documents could be exposed to unauthorized users.

**Existing controls:**
- Permission routes require authentication.
- The server verifies that the current user owns the document.
- Only Read and Edit permission values are accepted.
- Denied grant and revoke attempts are recorded.

**Security tests:** Permission-route tests cover grant and revoke authorization.

### Threat 5: Continued access after permission revocation

**Attack:** A user attempts to access a document after the owner has revoked their permission.

**Impact:** A user could retain access after it should have been removed.

**Existing controls:**
- Permission checks query current database records.
- Access is not based only on a previously displayed page or hidden interface element.
- Subsequent requests are checked against the updated permission records.

**Limitation:** Revocation prevents subsequent authorized requests. It cannot retrieve a document already downloaded or necessarily terminate a transfer that was already in progress.

### Threat 6: Privilege escalation

**Attack:** A Viewer or Owner attempts to access Admin routes or change another user's role.

**Impact:** Unauthorized administrative control.

**Existing controls:**
- Admin routes require authentication.
- The server checks the user's Admin role.
- Unauthorized Admin access attempts are recorded.
- The Admin creation script prevents creation of another Admin if one already exists.

**Security tests:** Role tests verify role restrictions.

### Threat 7: Malicious or disguised file uploads

**Attack:** A user uploads a file with an allowed extension but content that does not match the expected format.

**Impact:** Unsafe or invalid files could enter document storage.

**Existing controls:**
- Only PDF, DOC, DOCX, TXT, PNG, JPG, and JPEG extensions are allowed.
- Maximum upload size is 10 MB.
- The server checks file content signatures or structure for supported formats.
- Uploaded filenames are sanitized.

**Accepted risk:** File-format validation does not replace antivirus or malware scanning. Uploaded files are not guaranteed to be malware-free.

### Threat 8: Password exposure

**Attack:** An attacker obtains access to the user database.

**Impact:** User credentials could be compromised.

**Existing controls:**
- Passwords are stored as Werkzeug password hashes rather than plaintext.
- Account-creation scripts request passwords without displaying them in the terminal.
- The scripts require passwords of at least 12 characters.

**Remaining risk:** Password hashing does not prevent brute-force login attempts. Rate limiting and multi-factor authentication are future improvements.

### Threat 9: Audit-log tampering

**Attack:** Someone modifies an existing audit event or changes its link to the previous event.

**Impact:** Evidence of security incidents could become unreliable.

**Existing controls:**
- Audit events use HMAC-SHA256 signatures.
- Each signed event includes a link to the previous signed event.
- Verification checks event hashes and previous-hash links.
- Automated tests detect modified event details and broken previous-hash links.

**Limitations:**
- Historical audit entries created before hash protection was introduced are legacy entries and are not cryptographically verified.
- The HMAC secret must remain confidential.
- An attacker who compromises the application and its secret may be able to forge new valid events.
- Without an external immutable checkpoint, deletion or truncation of the latest events may not be detected.
- Independent, append-only audit storage is a future improvement.

## 5. Role-Based Access Control

### Admin
- Can access the Admin dashboard.
- Can manage users and roles.
- Can view audit logs.
- Does not automatically receive access to every private document.

### Owner
- Can upload documents.
- Can view, edit, and delete owned documents.
- Can grant Read or Edit permission to another registered user.
- Can revoke document-specific permissions.

### Viewer
- Can access documents explicitly shared with them.
- Read permission allows viewing and downloading.
- Edit permission allows viewing, downloading, and editing document metadata.
- Cannot delete documents or change sharing permissions unless separately authorized as the owner.

## 6. Audit Logging

The application records important security activities, including:

- Document uploads.
- Document downloads.
- Document edits.
- Document deletions.
- Permission grants and revocations.
- Role changes.
- Denied access attempts on protected operations.

Audit records can include the actor, document, action, outcome, timestamp, IP address, and event details, depending on the event.

The integrity mechanism uses HMAC-SHA256 and previous-event hashes for signed events.

Legacy events created before this mechanism was introduced are not cryptographically verified.

## 7. Security Testing

The automated test suite includes coverage for:

- Application basics.
- User registration.
- Login and logout.
- Role restrictions.
- Document ownership.
- Document operations.
- Permission grants and revocations.
- Unauthorized access attempts.
- Audit-chain integrity.

Three dedicated audit-integrity tests verify:
1. A valid signed audit chain passes verification.
2. Modified event details fail verification.
3. An incorrect previous-event hash fails verification.

**Latest recorded full test result: 60 passed.**

Tests are useful evidence of the implemented controls, but they do not prove the absence of every security vulnerability. The deployed application should also be tested against direct unauthorized HTTP requests.

## 8. Accepted Risks and Future Improvements

The following protections are not claimed as implemented unless separately verified:

| Protection | Status |
|---|---|
| Multi-factor authentication | Future improvement |
| Login rate limiting and account lockout | Future improvement |
| Malware scanning | Future improvement |
| Encryption at rest | Future improvement |
| Independent immutable audit storage | Future improvement |
| External audit checkpoints | Future improvement |
| Production HTTPS and deployment hardening | Requires deployment verification |
| Automated backup and recovery | Future improvement |
| Security monitoring and alerting | Future improvement |

Other accepted risks include:
- A user who is authorized to download a document may retain a local copy after access is revoked.
- Compromise of the application server or its secret key can undermine audit integrity.
- A database administrator with sufficient privileges may modify or delete stored records.
- Automated tests cannot replace a complete security review.

## 9. Security Design Principle

TrustVault follows a server-side authorization principle:

**Every protected document operation must verify the current user's identity, role, ownership, or explicit document permission before allowing the operation.**

The interface is not treated as a security boundary. Authorization must remain effective even when a user sends requests directly to the application endpoints.
