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
