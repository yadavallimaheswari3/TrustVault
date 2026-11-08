
# TrustVault – AI Prompt Log

This file records how AI assistance was used during TrustVault development, the issues identified, and the fixes applied. Prompt descriptions are summaries, not verbatim transcripts.

## Entry 1: Day 1 – Project Setup and Registration
**Date:** 2026-11-02

**Prompt summary:** Asked AI for beginner-friendly, step-by-step guidance to create the TrustVault Flask project and implement user registration.

**AI output:** Suggested Flask project structure, database setup, user registration, input validation, password hashing, and database migrations.

**Problems identified:** Initial tests exposed CSRF-related test failures. Security configuration and secret handling also needed attention.

**Fix applied:** Adjusted test configuration while retaining CSRF protection in the application. Updated `.gitignore` and environment configuration.

**Testing:** Registration and application tests were run.

**Commit:** https://github.com/yadavallimaheswari3/TrustVault/commit/fd56f7e

---

## Entry 2: Day 2 – Login and Logout
**Date:** 2026-11-05

**Prompt summary:** Asked AI to implement secure login and logout functionality.

**AI output:** Login and logout routes using Flask-Login and password-hash verification.

**Problems identified:** Login behavior needed separate tests for valid credentials, invalid credentials, and logout.

**Fix applied:** Added dedicated login tests and checked authentication behavior.

**Testing:** Login tests and the project test suite were run.

**Commit:** https://github.com/yadavallimaheswari3/TrustVault/commit/40c67e4

---

## Entry 3: Day 2 – Role-Based Security
**Date:** 2026-11-05

**Prompt summary:** Asked AI to introduce Admin, Owner, and Viewer roles.

**AI output:** Suggested role constants, a default Viewer role, and database role validation.

**Problems identified:** Invalid roles must not be accepted, and users must not receive elevated privileges by default.

**Fix applied:** Added role validation and tests for role restrictions.

**Testing:** Role-related tests were run.

**Commit:** https://github.com/yadavallimaheswari3/TrustVault/commit/8ca8446

---

## Entry 4: Day 3 – Document Permissions and Audit Logging
**Date:** 2026-11-06

**Prompt summary:** Asked AI to help implement document-level permissions and record document-related activities.

**AI output:** Suggested document permission records and audit log functionality.

**Problems identified:** Access must be checked for each document. Unauthorized access attempts also need to be recorded.

**Fix applied:** Implemented permission-related functionality and audit logging.

**Testing:** Permission and audit-related tests were added and executed.

**Commit:** https://github.com/yadavallimaheswari3/TrustVault/commit/5b884d4

---

## Entry 5: Day 3 – Secure Document Upload
**Date:** 2026-11-06

**Prompt summary:** Asked AI to implement secure document uploads with validation.

**AI output:** Suggested upload routes, file validation, storage handling, and document ownership.

**Problems identified:** Upload validation and ownership checks are important to prevent unsafe files and unauthorized operations.

**Fix applied:** Implemented upload validation and tests for document uploads.

**Testing:** Upload validation tests were run.

**Commit:** https://github.com/yadavallimaheswari3/TrustVault/commit/db46d9b

---

## Entry 6: Day 3 – Document Search and Access-Control Testing
**Date:** 2026-11-06

**Prompt summary:** Asked AI to implement document search using filters.

**AI output:** Suggested search by document name, owner, category, and date.

**Problems identified:** Search results must not expose documents belonging to users who do not have permission to access them.

**Fix applied:** Applied access filtering to search results and added document route tests.

**Testing:** Search and document access tests were run.

**Commit:** https://github.com/yadavallimaheswari3/TrustVault/commit/a012da5

---

## Entry 7: Day 4 – Document Editing, Deletion, and Admin Audit Logs
**Date:** 2026-11-07

**Prompt summary:** Asked AI to implement document editing, deletion, and administrative audit log access.

**AI output:** Suggested document update and delete routes and admin audit log functionality.

**Problems identified:** Users must not be able to modify or delete documents they do not own. Administrative audit routes must require the Admin role.

**Fix applied:** Added ownership and role checks and related tests.

**Testing:** Document route and admin audit log tests were run.

**Commits:**
- https://github.com/yadavallimaheswari3/TrustVault/commit/0b36339
- https://github.com/yadavallimaheswari3/TrustVault/commit/494af96

---

## Entry 8: Day 5 – Secure Document Dashboard
**Date:** 2026-11-07

**Prompt summary:** Asked AI to improve the dashboard and ensure users only see documents they are allowed to access.

**AI output:** Suggested a protected dashboard using document access checks.

**Problems identified:** A dashboard must not expose private documents simply because they exist in the database.

**Fix applied:** Added authentication and document visibility checks.

**Testing:** Dashboard and application tests were run.

**Commits:**
- https://github.com/yadavallimaheswari3/TrustVault/commit/65c7719
- https://github.com/yadavallimaheswari3/TrustVault/commit/2989096

---

## Entry 9: Day 6 – Audit Log Integrity Protection
**Date:** 2026-11-08

**Prompt summary:** Asked AI to improve audit log integrity so that modifications to recorded events can be detected.

**AI output:** Suggested HMAC-SHA256 event hashes and hash chaining using previous event hashes.

**Problems identified:**
- Modified audit event details must be detectable.
- Broken links between audit events must be detected.
- Existing unsigned audit records need to be handled honestly.
- Database timestamps needed consistent normalization during verification.

**Fix applied:** Added audit integrity fields, HMAC-based event verification, timestamp normalization, and a database migration. Added tests for valid chains, modified events, and broken previous hashes.

**Testing:** All three audit integrity tests passed. The complete project test suite passed with 60 tests.

**Commit:** https://github.com/yadavallimaheswari3/TrustVault/commit/3006c60

---

## Entry 10: Day 6 – Documentation and Threat Model
**Date:** 2026-11-08

**Prompt summary:** Asked AI to help document the actual application features, route permissions, setup instructions, security threats, and known limitations.

**AI output:** Helped organize the README and threat model documentation.

**Problems identified:** Security documentation must not claim protections that the application does not implement. Limitations such as unsigned legacy audit records and the absence of an external immutable audit checkpoint must be disclosed.

**Fix applied:** Updated README.md and THREATS.md to describe implemented protections, setup instructions, testing, and accepted risks.

**Commits:**
- https://github.com/yadavallimaheswari3/TrustVault/commit/efa8261
- https://github.com/yadavallimaheswari3/TrustVault/commit/b3c907b
