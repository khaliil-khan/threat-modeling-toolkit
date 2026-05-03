# 📧 Email Configuration Guide - Password Reset Emails

## Overview
The Threat Toolkit now sends password reset emails to users via SMTP. You can use Gmail, Outlook, or any email provider.

---

## Quick Setup (Choose One)

### ✅ Option 1: Gmail (Recommended for Personal Use)

**Step 1: Enable 2-Step Verification**
1. Go to: https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow the steps

**Step 2: Generate App Password**
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Google will generate a 16-character password
4. Copy it (it has spaces, that's normal)

**Step 3: Update `.env` file**
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx
```

**Step 4: Restart Container**
```bash
docker compose down
docker compose up -d
```

---

### ✅ Option 2: Outlook/Hotmail

**Step 1: Enable 2-Step Verification**
1. Go to: https://account.microsoft.com/security
2. Click "Advanced security options"
3. Enable 2-Step Verification

**Step 2: Create App Password**
1. Go to: https://account.microsoft.com/security
2. Click "App passwords"
3. Select "Mail" and "Windows"
4. Copy the generated password

**Step 3: Update `.env` file**
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SENDER_EMAIL=your-email@outlook.com
SENDER_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**Step 4: Restart Container**
```bash
docker compose down
docker compose up -d
```

---

### ✅ Option 3: Student/Academic Email

Most universities use one of these systems:

#### **Office 365 (Most Common)**
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SENDER_EMAIL=your-name@university.edu
SENDER_PASSWORD=your-university-password
```

#### **Google Workspace (Some Universities)**
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-name@university.edu
SENDER_PASSWORD=your-app-password
```

**📝 Note:** Contact your university's IT department for exact SMTP settings if neither works.

---

### ✅ Option 4: Corporate / Custom Email

For company email or custom domains:

```
SMTP_SERVER=mail.yourcompany.com    # Ask IT support
SMTP_PORT=587
SENDER_EMAIL=noreply@yourcompany.com
SENDER_PASSWORD=your-app-password
```

---

## Testing Email Sending

### Test 1: Check Docker Logs
```bash
docker logs threat-toolkit
```

Look for one of these messages:

✅ **Success:**
```
✓ Password reset email sent to user@example.com
```

⚠️ **Not Configured:**
```
⚠️ Email not sent - SMTP not configured
📧 Reset link for user@example.com: http://...
```

❌ **Authentication Failed:**
```
✗ SMTP Authentication failed - check email/password
```

### Test 2: Test Via Web UI
1. Open: http://13.63.73.247:5000/auth/forgot-password
2. Enter your email address
3. Submit the form
4. Check your email inbox and spam folder

---

## Common Issues & Solutions

### ❌ "Authentication failed"
**Cause:** Wrong email or password  
**Fix:** 
- Double-check SENDER_EMAIL and SENDER_PASSWORD in .env
- For Gmail: Make sure you used App Password, not regular password
- For Outlook: Make sure 2FA is enabled

### ❌ "Connection refused"
**Cause:** Wrong SMTP server or port  
**Fix:**
- Gmail: Use `smtp.gmail.com:587`
- Outlook: Use `smtp-mail.outlook.com:587`
- Make sure port is `587` (not 25, 465, or 993)

### ❌ "Email not received"
**Check:**
1. Spam/Junk folder
2. Check Docker logs: `docker logs threat-toolkit`
3. Verify SENDER_EMAIL and recipient email are different

### ❌ "SSL/TLS error"
**Fix:** Make sure SMTP_PORT is `587` not `465`

---

## Production Deployment Checklist

- [ ] Generated app password (don't use regular password!)
- [ ] Updated .env file with SMTP settings
- [ ] Tested email sending locally
- [ ] Restarted Docker container
- [ ] Tested password reset flow end-to-end
- [ ] Checked spam filters for test emails

---

## Email Format

Users will receive emails that include:
- ✓ Personalized greeting with username
- ✓ Clickable button to reset password
- ✓ Direct link for copy-paste
- ✓ 1-hour expiration warning
- ✓ Professional HTML formatting
- ✓ Plain text fallback

---

## Support

If emails still aren't working:

1. **Check SMTP configuration:**
   ```bash
   docker exec threat-toolkit python -c "import os; print(f'Server: {os.environ.get(\"SMTP_SERVER\")}'); print(f'Port: {os.environ.get(\"SMTP_PORT\")}'); print(f'Email: {os.environ.get(\"SENDER_EMAIL\")}')"
   ```

2. **View container logs for errors:**
   ```bash
   docker logs threat-toolkit 2>&1 | grep -E "(✓|✗|⚠️)"
   ```

3. **Test SMTP connection locally:**
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   print("✓ Connection successful!")
   ```

---

## Security Notes

- 🔒 Never commit `.env` file to Git (it's in .gitignore)
- 🔒 Use App Passwords, not regular passwords
- 🔒 Enable 2-Step Verification on your email account
- 🔒 Rotate app passwords periodically
- 🔒 Use strong, unique passwords

---

## Next Steps

After email is configured, test the complete flow:

1. Go to http://13.63.73.247:5000/auth/forgot-password
2. Enter your email
3. Check your inbox
4. Click the reset link
5. Set a new password
6. Login with new credentials

✅ **All done!** Password reset with emails is now working.
