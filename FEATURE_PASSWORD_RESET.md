# Password Reset Feature - Complete Implementation Guide

## Overview
This document describes the complete "Forgot Password" feature implementation added to the Threat Toolkit application.

---

## Feature Summary
**What**: Users can now reset their forgotten passwords via secure email links  
**Why**: Improves user experience and security by allowing password recovery  
**Who**: Any user without admin credentials  
**When**: Available on the login page via "Forgot Password?" link

---

## Architecture & Implementation Details

### 1. Database Layer (`app/models.py`)

#### Changes to User Model:
```python
# New columns added:
reset_token = db.Column(db.String(256), nullable=True)           # Secure reset token
reset_token_expiry = db.Column(db.DateTime, nullable=True)       # Token expiration time
```

#### New Methods:

**`generate_reset_token()`**
- Generates a secure token using `itsdangerous.URLSafeTimedSerializer`
- Token is bound to user's email for extra security
- Sets expiration to 1 hour from generation time
- Returns the token string

**`verify_reset_token(token)`**
- Validates if token exists, hasn't expired, and matches stored token
- Uses cryptographic verification
- Auto-clears expired tokens from database
- Returns user's email if valid, None otherwise

---

### 2. Forms Layer (`app/auth/forms.py`)

#### ForgotPasswordForm
- **Fields**: email (required, must be valid email format)
- **Purpose**: User requests password reset
- **Validation**: Email must exist in system

#### ResetPasswordForm
- **Fields**: 
  - password (8-100 chars, must contain uppercase, lowercase, numbers)
  - confirm (must match password)
- **Purpose**: User enters new password
- **Validation**: 
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - Passwords must match

---

### 3. Routes/Views Layer (`app/auth/routes.py`)

#### New Endpoints:

**POST/GET `/forgot-password`**
```
Purpose: Request password reset
Flow:
  1. User enters email
  2. System checks if email exists
  3. Generates reset token
  4. Sends email with reset link (or logs it in dev mode)
  5. Shows confirmation message (doesn't reveal if email exists)
Returns: Redirect to login or forgot_password form
Security: Rate limiting, logs all attempts
```

**POST/GET `/reset-password/<token>`**
```
Purpose: Reset password using token
Flow:
  1. System validates token
  2. User enters new password
  3. Password hashed and stored
  4. Token cleared from database
  5. User redirected to login
Returns: Success page or error page
Security: Token validation, password requirements
```

#### Helper Function:

**`send_reset_email(user, reset_token)`**
- Sends HTML + plain text email with reset link
- Development mode: Logs to application logs instead of sending
- Production mode: Sends via SMTP with credentials
- Email includes:
  - Personalized greeting
  - Reset link with token
  - 1-hour expiration warning
  - Security disclaimer

---

### 4. Templates Layer (`app/templates/auth/`)

#### forgot_password.html
- Clean form for email entry
- Includes helpful text
- Links to login and register pages
- Responsive design with animations

#### reset_password.html
- Password entry form with confirmation
- Shows password requirements
- Security guidelines
- Link back to login

#### login.html (UPDATED)
- Added "Forgot Password?" link next to "Remember me"
- Links to `/forgot-password` endpoint
- Positioned for easy discovery

---

## Security Features

### 1. Token Security
- Tokens are cryptographically signed using application SECRET_KEY
- Bound to specific user email
- Time-limited (1 hour expiration)
- Single-use (cleared after successful reset)

### 2. Password Security
- Passwords hashed with PBKDF2:SHA256
- Multiple complexity requirements
- No storage of plaintext passwords
- Salting included automatically

### 3. Access Control
- Unauthenticated users only (redirects logged-in users)
- Rate limiting prevents brute force
- Failed attempts logged
- Email existence not revealed (security best practice)

### 4. Logging & Audit Trail
- All password resets logged with timestamp
- Failed attempts recorded
- User identifiers tracked
- Useful for security investigations

---

## Data Flow Diagram

```
User visits /forgot-password
         ↓
   Enters email
         ↓
   System validates email exists
         ↓
   generate_reset_token() called
         ↓
   Token + expiry stored in database
         ↓
   send_reset_email() triggered
         ↓
   ┌─────────────────────────┐
   │   Dev Mode:             │  Prod Mode:
   │   Log to console        │  Send via SMTP
   └─────────────────────────┘
         ↓
   User receives email with link
         ↓
   User clicks link → /reset-password/<token>
         ↓
   System calls verify_reset_token()
         ↓
   ✓ Valid? Show form : Show error
         ↓
   User enters new password
         ↓
   Password hashed + stored
         ↓
   Token cleared from DB
         ↓
   Redirect to login
```

---

## Database Changes

```sql
-- New columns added to users table:
ALTER TABLE users ADD COLUMN reset_token VARCHAR(256);
ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME;

-- Indexes (automatic, improve lookup speed):
-- When querying by reset_token for verification
```

---

## Environment Variables (Optional for Production)

```bash
# SMTP Configuration (if not using localhost)
SMTP_SERVER=smtp.gmail.com              # Default: localhost
SMTP_PORT=587                           # Default: 587
SENDER_EMAIL=noreply@threat-toolkit.com # Default: noreply@threat-toolkit.local
SENDER_PASSWORD=your-password           # Default: empty (dev mode)

# Application Security
SECRET_KEY=your-secret-key-here         # For token generation
```

---

## Testing the Feature

### Manual Testing Steps:

1. **Test Forgot Password Form**
   - Navigate to login page
   - Click "Forgot Password?"
   - Enter valid email
   - Check console logs for reset link (dev mode)

2. **Test Reset Password**
   - Copy reset link from logs
   - Open in browser
   - Enter new password
   - Verify password requirements feedback
   - Log in with new password

3. **Test Token Expiration**
   - Generate reset token
   - Wait 1+ hours (or modify code to 1 minute for testing)
   - Try using old token
   - Should show "Invalid or expired reset link"

4. **Test Security**
   - Try modifying token in URL
   - Try accessing /reset-password without token
   - Try reusing expired token
   - All should fail gracefully

---

## Files Modified/Created

### Modified Files:
- `app/models.py` - Added reset token fields and methods
- `app/auth/forms.py` - Added 2 new forms
- `app/auth/routes.py` - Added 2 new routes + email function
- `app/templates/auth/login.html` - Added "Forgot Password?" link

### Created Files:
- `app/templates/auth/forgot_password.html` - Email request form
- `app/templates/auth/reset_password.html` - Password reset form
- `migrate_db.py` - Database migration script

---

## Code Quality & Standards

### Best Practices Implemented:
✅ Security by design (no email leakage, strong tokens)  
✅ Rate limiting to prevent abuse  
✅ Comprehensive error handling  
✅ Logging for audit trail  
✅ Password complexity requirements  
✅ Single responsibility principle  
✅ DRY (Don't Repeat Yourself)  
✅ Responsive UI with animations  
✅ Works in dev and prod modes  
✅ No external service dependencies (email logging fallback)  

### Error Handling:
- Invalid tokens → Clear error message
- Expired tokens → Prompt to request new one
- SMTP failures (prod) → Graceful fallback
- Rate limiting → Informative message
- Database errors → Logged, user sees generic error

---

## Integration Points

### With Existing Code:
1. **Authentication**: Uses existing Flask-Login
2. **Database**: Uses existing SQLAlchemy setup
3. **Forms**: Uses existing Flask-WTF setup
4. **Templates**: Extends base.html template
5. **Rate Limiting**: Uses existing rate limit logic from login/register

### No Breaking Changes:
- All existing functionality intact
- Backward compatible
- No API changes
- Works with existing deployment

---

## Maintenance & Future Improvements

### Current Limitations:
- Tokens stored in database (not in JWT)
- Single email backend
- No SMS alternative

### Future Enhancements (Optional):
1. Add admin panel to view reset requests
2. Implement SMS as backup
3. Add 2FA to password reset
4. Email templates as separate files
5. Rate limiting per email

---

## Troubleshooting

### Issue: "Invalid or expired reset link"
**Causes**: Token expired, database cleared, wrong URL  
**Solution**: Request new password reset

### Issue: Email not received
**Dev Mode**: Check console logs for URL  
**Prod Mode**: Check SMTP settings, check spam folder

### Issue: Password requirements not met
**Solution**: Ensure password has uppercase, lowercase, and number

---

## Dependencies Used

- `itsdangerous` - Already in requirements.txt (for token generation)
- `smtplib` - Built-in Python (for email)
- `email.mime` - Built-in Python (for email formatting)

---

## Deployment Checklist

- [ ] Database migrated (`python migrate_db.py`)
- [ ] All files committed to git
- [ ] Tested in development mode
- [ ] Tested all error cases
- [ ] Updated SECRET_KEY in production
- [ ] (Optional) Configure SMTP for email sending
- [ ] Monitor logs for errors
- [ ] Test email delivery in production

