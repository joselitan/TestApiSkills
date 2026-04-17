# User Registration and Email Verification

## Overview

This document describes the user self-registration and email verification functionality implemented in the QA platform. It also explains the SMTP behavior, current limitations, and the key functions/files involved.

## Implemented Functionality

### 1. User Registration

- Endpoint: `POST /api/register`
- File: `src/app.py`
- Function: `register()`

Description:
- Validates incoming JSON payload.
- Accepts `email`, `password`, `confirm_password`, optional `username`, and optional `role`.
- Normalizes email to lowercase.
- If username is missing, derives one from the email local part.
- Enforces rules:
  - `email`, `password`, `confirm_password` are required
  - password and confirm password must match
  - password must be at least 8 characters long
  - email must be valid
  - role must be in `app.config["ALLOWED_ROLES"]`
  - `admin` role is explicitly disallowed
- Stores the user in the database as inactive (`is_active = 0`).
- Generates an email verification token and stores it in the database.
- Attempts to send a verification email.
- Returns `201` with a success or email-sending warning message.

### 2. Email Verification

- Endpoint: `GET /api/verify-email`
- File: `src/app.py`
- Function: `verify_email()`

Description:
- Accepts a `token` query parameter.
- Verifies the token using `itsdangerous.URLSafeTimedSerializer`.
- If valid, activates the corresponding user by setting `is_active = 1`.
- Clears the verification token and expiration timestamp.

### 3. Login Protection Until Verification

- Endpoint: `POST /api/login`
- File: `src/app.py`
- Function: `login()`

Description:
- Accepts login credentials with either `email` or `username` plus `password`.
- Checks the password hash.
- Rejects login when `user["is_active"]` is false.
- Returns `403` with message `Account not active. Verify your email.` for inactive users.

### 4. Password Reset Flow

- Endpoint: `POST /api/password-reset-request`
- File: `src/app.py`
- Function: `password_reset_request()`

Description:
- Accepts `email`.
- If the email exists, generates a reset token and expiration.
- Sends a password reset email.
- Always returns `200` to avoid leaking whether the email exists.

- Endpoint: `POST /api/password-reset`
- File: `src/app.py`
- Function: `password_reset()`

Description:
- Accepts `token`, `password`, `confirm_password`.
- Validates token and password input.
- Updates the stored password hash when successful.

## SMTP and Email Delivery

### Email Functions

- `send_email(to, subject, body)`
- `send_verification_email(email, token)`
- `send_password_reset_email(email, token)`
- File: `src/app.py`

Description:
- `send_email()` is the core SMTP function.
- Uses `smtplib.SMTP` or `smtplib.SMTP_SSL` depending on configuration.
- Logs errors when sending fails.
- Returns a boolean indicating whether the email send attempt succeeded.

### Configuration

The application reads SMTP-related settings from environment variables:

- `EMAIL_HOST`
- `EMAIL_PORT` (default `587`)
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`
- `EMAIL_FROM` (default `noreply@example.com`)
- `EMAIL_USE_TLS` (default `true`)
- `EMAIL_USE_SSL` (default `false`)
- `EMAIL_DEBUG` (default `false`)

### `EMAIL_DEBUG` Behavior

- When `EMAIL_DEBUG=true`, the app will not require `EMAIL_HOST` or `EMAIL_USERNAME` to be present.
- Instead it logs the email contents and returns success from `send_email()`.
- This is useful for development when SMTP is not configured.

## Database Support

- File: `src/database.py`
- Relevant schema: `users` table

Fields added or used:
- `email`
- `role`
- `is_active`
- `verification_token`
- `verification_expires_at`
- `password_reset_token`
- `password_reset_expires_at`

The database initialization and migration logic ensures these columns exist.

## Frontend Components

The user registration and account flows are supported by templates:
- `templates/register.html`
- `templates/login.html`
- `templates/reset_password_request.html`
- `templates/reset_password.html`

These pages let users register, request a reset, and submit a new password.

## Current Limits and Notes

### 1. SMTP dependency
- The app does not include a built-in Mailinator relay or API.
- Mailinator is only a recipient inbox service.
- The platform requires a working outbound SMTP server to send real emails.
- If SMTP is missing, registration still creates the user, but verification email delivery fails.

### 2. Self-registration gating
- Controlled by `ENABLE_SELF_REGISTRATION` environment variable.
- Default is enabled.
- If disabled, `/api/register` returns `403`.

### 3. Account activation
- New accounts are inactive until email verification completes.
- Inactive accounts cannot log in.

### 4. Password policy
- Minimum password length is 8 characters.
- No additional complexity rules are enforced.

### 5. Role restrictions
- Allowed roles are defined by `app.config["ALLOWED_ROLES"]`.
- In the current setup, this is `['member', 'tester']`.
- Explicitly disallows `admin` role registration.

### 6. Debug mode behavior
- `EMAIL_DEBUG=true` is useful for local testing.
- It does not send real email, only logs the content.

## How to Test It

1. Enable SMTP environment variables.
2. Register a new user at `/register`.
3. Check that `/api/register` returns `Verification email sent.`
4. Use the token link from the verification email to activate the account.
5. Attempt login after verification.

If SMTP is unavailable, set `EMAIL_DEBUG=true` to see the email body in logs.
