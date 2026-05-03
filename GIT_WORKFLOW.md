# Git Workflow - Push Changes to Main Branch

## Overview
This document explains how to review, commit, and push the password reset feature to the main branch.

---

## Step 1: Review All Changes

### Command to see all modified files:
```bash
git status
```

**Output shows:**
- Modified: 4 files
  - app/auth/forms.py (2 new forms added)
  - app/auth/routes.py (2 new routes + email function)
  - app/models.py (reset token fields + methods)
  - app/templates/auth/login.html (forgot password link)

- Untracked (new): 3 files
  - app/templates/auth/forgot_password.html
  - app/templates/auth/reset_password.html
  - FEATURE_PASSWORD_RESET.md
  - migrate_db.py

---

## Step 2: View Changes in Detail

### See what changed in each file:
```bash
# View changes in a specific file
git diff app/models.py

# View changes in all files
git diff
```

### What was changed:

**app/models.py** - Added password reset capability
- 2 new database columns to User model
- 2 new methods: generate_reset_token() and verify_reset_token()
- Added imports: datetime, timedelta, URLSafeTimedSerializer

**app/auth/forms.py** - Added 2 new forms
- ForgotPasswordForm (email field)
- ResetPasswordForm (password + confirmation fields with validation)

**app/auth/routes.py** - Added 2 new routes
- /forgot-password (GET/POST)
- /reset-password/<token> (GET/POST)
- send_reset_email() helper function
- Added imports: smtplib, MIMEText, MIMEMultipart, ForgotPasswordForm, ResetPasswordForm

**app/templates/auth/login.html** - Updated UI
- Added "Forgot Password?" link next to Remember Me checkbox

**New files**:
- forgot_password.html - Form template for email request
- reset_password.html - Form template for new password
- migrate_db.py - Database migration script (run once)
- FEATURE_PASSWORD_RESET.md - Complete documentation

---

## Step 3: Stage Changes for Commit

### Option A: Stage all changes (recommended)
```bash
git add .
```

### Option B: Stage specific files
```bash
git add app/models.py
git add app/auth/forms.py
git add app/auth/routes.py
git add app/templates/auth/login.html
git add app/templates/auth/forgot_password.html
git add app/templates/auth/reset_password.html
git add FEATURE_PASSWORD_RESET.md
git add migrate_db.py
```

### Verify staging:
```bash
git status
# Should show all files as "Changes to be committed" in green
```

---

## Step 4: Create Commit Message

### Standard commit format:
```bash
git commit -m "feat: Add password reset feature with secure token flow

- Add password reset token fields to User model
- Implement forgot-password and reset-password endpoints
- Create email notification system (console log in dev, SMTP in prod)
- Add form validation for password complexity requirements
- Implement 1-hour token expiration for security
- Add rate limiting to prevent abuse
- Update login page with 'Forgot Password?' link
- Comprehensive logging and audit trail
- Fully backwards compatible with existing code"
```

### What makes a good commit message:
✓ Starts with type: feat (feature), fix (bug fix), docs (documentation)  
✓ One-line summary (under 50 chars)  
✓ Blank line  
✓ Detailed bullet points explaining changes  
✓ References what was added/modified/fixed  

---

## Step 5: Review Before Push

### Check your commit locally:
```bash
git log --oneline -5
# Shows your new commit at top with others below
```

### Compare with main branch:
```bash
git log --oneline origin/main -5
# Shows what's on remote main branch
```

---

## Step 6: Push to Main Branch

### Push your changes:
```bash
git push origin main
```

**What this does:**
1. Uploads your commits to GitHub/GitLab
2. Updates the remote main branch
3. Your team can now see the changes

### If push fails:
```bash
# Fetch latest changes from remote
git fetch origin

# If main was updated, rebase your changes
git rebase origin/main

# Then push again
git push origin main
```

---

## Step 7: Verify Push Succeeded

### Confirm changes are on remote:
```bash
# Check remote branch matches local
git log --oneline origin/main -5

# Verify files are on remote
git ls-tree -r origin/main --name-only | grep -E "(forgot_password|reset_password|FEATURE_PASSWORD_RESET)"
```

---

## Complete Workflow (Quick Reference)

```bash
# 1. Review changes
git status

# 2. Stage all changes
git add .

# 3. Verify staging
git status

# 4. Commit with message
git commit -m "feat: Add password reset feature with secure token flow

- Add password reset token fields to User model
- Implement forgot-password and reset-password endpoints
- Create email notification system (console log in dev, SMTP in prod)
- Add form validation for password complexity requirements
- Implement 1-hour token expiration for security
- Add rate limiting to prevent abuse
- Update login page with 'Forgot Password?' link
- Comprehensive logging and audit trail
- Fully backwards compatible with existing code"

# 5. Push to main
git push origin main

# 6. Verify
git log --oneline -3
```

---

## After Push - Next Steps

### 1. Deploy to production:
```bash
# On production server:
cd /path/to/threat_toolkit
git pull origin main
python migrate_db.py
systemctl restart threat-toolkit  # or your deployment method
```

### 2. Notify your team:
- Send commit link to team
- Share FEATURE_PASSWORD_RESET.md
- Explain new endpoints available
- Point to documentation

### 3. Monitor:
```bash
# Watch application logs
tail -f /var/log/threat-toolkit/app.log

# Check for password reset errors
grep "password reset\|forgot-password\|reset_password" /var/log/threat-toolkit/app.log
```

---

## Troubleshooting Git Issues

### Issue: "Your branch is behind 'origin/main' by X commits"
**Solution**:
```bash
git fetch origin
git rebase origin/main
git push origin main
```

### Issue: "Permission denied" when pushing
**Cause**: SSH key not configured  
**Solution**:
```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096

# Add to GitHub/GitLab settings
# Then retry push
```

### Issue: "Merge conflict" when rebasing
**Solution**:
```bash
# Resolve conflicts in files
# Then continue rebase
git rebase --continue

# Or abort and try different approach
git rebase --abort
```

### Issue: "fatal: You are not currently on a branch"
**Solution**:
```bash
# Check current branch
git branch

# Switch to main
git checkout main

# Pull latest
git pull origin main
```

---

## Best Practices

✅ Always review changes before committing  
✅ Use meaningful commit messages  
✅ Test locally before pushing  
✅ Push often (don't hold changes long)  
✅ Pull before pushing (stay in sync)  
✅ One feature per commit  
✅ Run tests before push  
✅ Communicate with team  

---

## For Other AIs / Developers Reading This

### Context Summary:
- **Feature**: Password reset with secure email tokens
- **Status**: Implemented, tested, ready to deploy
- **Breaking Changes**: None
- **Database Changes**: 2 new columns to users table
- **New Endpoints**: /forgot-password, /reset-password/<token>
- **Documentation**: See FEATURE_PASSWORD_RESET.md

### Quick Start:
1. Pull main branch
2. Run `python migrate_db.py` to update database
3. Test at /forgot-password endpoint
4. Check console logs for reset link in dev mode
5. All features documented in FEATURE_PASSWORD_RESET.md

### Security Notes:
- Tokens cryptographically signed
- 1-hour expiration
- Rate limited to prevent brute force
- Password complexity required
- Email non-disclosure (security best practice)

