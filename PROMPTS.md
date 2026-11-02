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