# TrustVault - AI Prompt Log

## Entry 1: Day 1 - Project Setup and Registration
**Date:** 2026-11-02

### 1. Prompt Summary
I asked AI to guide me step by step to build TrustVault using Flask. I wanted to set up the project, database, and user registration.

### 2. AI Output
AI helped me create:
- Flask application and project structure.
- Database connection and User table.
- User registration form.
- Email and password validation.
- Password hashing.
- Database migration setup.

### 3. Problems Identified

**Problem 1:** During registration testing, 9 tests failed because CSRF protection required a security token.

**Problem 2:** Git reported trailing whitespace in the database migration file.

**Problem 3:** I needed to protect secret keys, local database files, and private uploaded documents from being pushed to GitHub.

### 4. My Fix
- Disabled CSRF only for normal registration tests and kept a separate CSRF security test enabled.
- Removed the extra space from the migration file.
- Updated `.gitignore` to protect private files and local database files.

### 5. Testing
- All 10 registration tests passed.
- All 14 project tests passed.
- Checked Git status to make sure secret and local files were not included.

### 6. Commit Link
To be added after creating the Git commit.


## Entry 2: Day 2 - Login and Logout Testing
**Date:** 2026-11-05

### 1. Prompt Summary
I asked AI to guide me in adding login and logout functionality and creating automated tests.

### 2. AI Output
AI helped me create:
- Login form and login route.
- Login page.
- Logout route using POST.
- Automated tests for login and logout.

### 3. Problem Identified
Login and logout functionality did not have separate automated tests.

### 4. My Fix
I created `tests/test_login.py` and tested successful login, incorrect password, and logout.

### 5. Testing
- 3 login/logout tests passed.
- All 17 project tests passed.

### 6. Commit Link
To be added after creating the Git commit.


## Entry 3: Day 2 - Role-Based Security
**Date:** 2026-11-05

### 1. Prompt Summary
I asked AI to help implement Admin, Owner, and Viewer roles securely.

### 2. AI Output
AI helped me add role constants, a default viewer role, and a database constraint to allow only valid roles.

### 3. Problem Identified
The database needed protection against invalid user roles.

### 4. My Fix
I updated the User model with role restrictions and created automated tests for valid and invalid roles.

### 5. Testing
- 2 role tests passed.
- All 19 project tests passed.

### 6. Commit Link
To be added after creating the Git commit.


## Entry 4: Day 3 - Document Model and Ownership Validation

**Date:** 2026-11-06

### 1. Prompt Summary
I asked AI to guide me step by step in creating a Document database model and testing document ownership in TrustVault.

### 2. AI Output
AI helped me:
- Create a Document model using SQLAlchemy.
- Add document fields such as owner ID, original filename, storage key, category, file size and upload date.
- Establish a relationship between the Document and User models.
- Generate and apply a database migration.
- Write automated tests to validate document ownership.

### 3. Problems Identified

**Problem 1:** A document should not be saved without an owner.

**Problem 2:** I needed to verify that a document was correctly linked to its actual owner.

### 4. My Fix
- Added a test to verify that the database rejects a document without an owner.
- Added a test to verify that a saved document is linked to the correct user.
- Applied the database migration to create the documents table.

### 5. Testing
- All 4 role and document ownership tests passed.
- All 21 project tests passed.

### 6. Commit Link
To be added after creating the Git commit.



## Entry 5: Day 3 - Document Search and Access-Control Testing

**Date:** 2026-11-06

### 1. Prompt Summary
I asked AI to help implement document search with filters for document name, owner email, category, and upload date. I also wanted to ensure that users could only see documents they were authorized to access.

### 2. AI Output
AI helped me:
- Create a document search route using GET.
- Add filters for document name, owner email, category, and upload date.
- Check document-view permissions before including a document in search results.
- Create automated tests for search functionality and access control.

### 3. Problems Identified

**Problem 1:** Search results must not expose private documents belonging to other users.

**Problem 2:** Search filters must return the correct documents when multiple filters are used together.

### 4. My Fix
- Added an access-permission check before returning each search result.
- Added a test to verify that document name, owner, category, and date filters work together.
- Added a security test to verify that a viewer cannot find an unshared private document.

### 5. Testing
- All 13 document-route tests passed.
- All 44 project tests passed.

### 6. Commit Link
To be added after creating the Git commit.


## Entry 6: Day 5 - Admin Audit Logs and Security Testing

**Date:** 2026-11-07

### 1. Prompt Summary
I asked AI to guide me in implementing an admin-only audit log viewing endpoint and writing automated security tests for it.

### 2. AI Output
AI helped me:
- Create an admin audit logs route at `/admin/audit-logs`.
- Restrict audit log access to authenticated administrators.
- Add filters for action and outcome.
- Return the latest 100 audit log entries.
- Validate the outcome filter to accept only allowed and denied.
- Write automated tests for admin access, unauthorized user access, and invalid filters.

### 3. Problems Identified

**Problem 1:** Normal users must not be allowed to view admin audit logs.

**Problem 2:** Invalid audit log filter values must be rejected.

**Problem 3:** Running pytest directly caused a ModuleNotFoundError because Python could not locate the app package.

### 4. My Fix
- Registered the admin blueprint in the Flask application.
- Added an admin role check to protect the audit logs endpoint.
- Added automated tests for admin access, viewer access rejection, and invalid outcome filters.
- Used `python -m pytest` to run tests through the active virtual environment.

### 5. Testing
- All 12 role and admin-related tests passed.
- All 50 project tests passed.

### 6. Commit Link
https://github.com/yadavallimaheshwari3/TrustVault/commit/494af96